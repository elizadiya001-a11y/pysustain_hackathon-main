"""
src/supabase_client.py
----------------------
Database and Storage Access Layer for FASAL AI using the official Supabase Python SDK.
Handles connection pooling, pagination, safe queries, RLS compliance, and error recovery.
"""

import os
import io
import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FasalSupabaseClient")

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "field-uploads")

_client_instance = None


def get_supabase_client():
    """
    Returns an initialized Supabase Client singleton.
    Returns None if credentials are missing or connection fails.
    """
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase URL or Key not configured in environment variables.")
        return None

    # Handle if URL has dashboard format
    api_url = SUPABASE_URL
    if "supabase.com/dashboard/project/" in api_url:
        proj_id = api_url.rstrip("/").split("/")[-1]
        api_url = f"https://{proj_id}.supabase.co"

    try:
        from supabase import create_client, Client
        _client_instance = create_client(api_url, SUPABASE_KEY)
        logger.info(f"Connected to Supabase client at {api_url}")
        return _client_instance
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def fetch_table(
    table_name: str,
    select: str = "*",
    filters: Optional[Dict[str, Any]] = None,
    order_col: Optional[str] = None,
    ascending: bool = True,
    page_size: int = 1000,
    max_records: Optional[int] = None
) -> Tuple[pd.DataFrame, bool]:
    """
    Safely retrieves records from a Supabase table with pagination.
    Returns (DataFrame, is_success).
    """
    client = get_supabase_client()
    if client is None:
        return pd.DataFrame(), False

    all_rows = []
    start = 0

    try:
        while True:
            end = start + page_size - 1
            query = client.table(table_name).select(select)

            if filters:
                for col, val in filters.items():
                    query = query.eq(col, val)

            if order_col:
                query = query.order(order_col, desc=not ascending)

            query = query.range(start, end)
            response = query.execute()

            rows = response.data or []
            all_rows.extend(rows)

            if len(rows) < page_size:
                break

            if max_records and len(all_rows) >= max_records:
                all_rows = all_rows[:max_records]
                break

            start += page_size

        df = pd.DataFrame(all_rows)
        return df, True
    except Exception as e:
        logger.error(f"Error fetching table '{table_name}': {e}")
        return pd.DataFrame(), False


def check_connection_health() -> Dict[str, Any]:
    """
    Verifies Supabase connection and checks row counts for core agricultural tables.
    """
    client = get_supabase_client()
    if client is None:
        return {
            "connected": False,
            "error": "Missing SUPABASE_URL or SUPABASE_KEY environment variables.",
            "tables": {}
        }

    tables_to_check = ["farms", "soil", "weather", "market_prices", "satellite_data", "soil_types"]
    table_status = {}

    for tbl in tables_to_check:
        try:
            res = client.table(tbl).select("*", count="exact").limit(1).execute()
            table_status[tbl] = {
                "accessible": True,
                "count": res.count if hasattr(res, "count") else len(res.data)
            }
        except Exception as e:
            table_status[tbl] = {
                "accessible": False,
                "error": str(e)
            }

    # Check recommendations_history table
    try:
        res = client.table("recommendations_history").select("*", count="exact").limit(1).execute()
        table_status["recommendations_history"] = {
            "accessible": True,
            "count": res.count if hasattr(res, "count") else len(res.data)
        }
    except Exception:
        table_status["recommendations_history"] = {
            "accessible": False,
            "pending_migration": True,
            "note": "Table not created yet. Run sql/reviewed_migrations.sql in Supabase SQL Editor."
        }

    return {
        "connected": True,
        "api_url": SUPABASE_URL,
        "tables": table_status
    }


def upload_field_image(file_bytes: bytes, file_name: str, content_type: str = "image/jpeg") -> Optional[str]:
    """
    Uploads a field image to Supabase Storage private/public bucket.
    Returns the public or signed URL if successful, else None.
    """
    client = get_supabase_client()
    if client is None:
        return None

    try:
        # Check / Ensure bucket
        try:
            client.storage.create_bucket(STORAGE_BUCKET, options={"public": False})
        except Exception:
            pass  # Bucket likely already exists

        # Upload file
        clean_name = f"uploads/{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
        res = client.storage.from_(STORAGE_BUCKET).upload(
            clean_name,
            file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )

        # Create a signed URL valid for 24 hours
        try:
            signed_url_res = client.storage.from_(STORAGE_BUCKET).create_signed_url(clean_name, 86400)
            return signed_url_res.get("signedURL") or signed_url_res.get("signedUrl")
        except Exception:
            return clean_name
    except Exception as e:
        logger.error(f"Error uploading image to Supabase Storage: {e}")
        return None


def save_recommendation_to_db(record: Dict[str, Any]) -> bool:
    """
    Persists a farmer recommendation report to recommendations_history.
    Returns True if successfully inserted into Supabase, False otherwise.
    """
    client = get_supabase_client()
    if client is None:
        return False

    try:
        res = client.table("recommendations_history").insert(record).execute()
        return bool(res.data)
    except Exception as e:
        logger.warning(f"Could not save to recommendations_history (table may need migration): {e}")
        return False


def fetch_recommendation_history(limit: int = 50) -> pd.DataFrame:
    """
    Fetches recent recommendation history records from Supabase.
    """
    df, success = fetch_table(
        "recommendations_history",
        order_col="created_at",
        ascending=False,
        max_records=limit
    )
    return df if success else pd.DataFrame()

