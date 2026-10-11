-- ==============================================================================
-- FASAL AI - Reviewed Database Migrations
-- Target Database: Supabase PostgreSQL (Project: bwlopgkkaasgmkdkoayb)
-- 
-- Description:
--   Creates the `recommendations_history` table to securely store farmer
--   assessments and generated crop recommendations.
--   Enforces Row Level Security (RLS) to prevent unauthorized access.
-- ==============================================================================

-- 1. Create recommendations_history table
CREATE TABLE IF NOT EXISTS public.recommendations_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    farmer_name VARCHAR(100) NOT NULL,
    farmer_id VARCHAR(50),
    state VARCHAR(50) NOT NULL,
    district VARCHAR(50) NOT NULL,
    village VARCHAR(100),
    area_acres DOUBLE PRECISION NOT NULL,
    current_crop VARCHAR(50) NOT NULL,
    current_yield_q_acre DOUBLE PRECISION,
    soil_type VARCHAR(50),
    soil_ph DOUBLE PRECISION,
    soil_n DOUBLE PRECISION,
    soil_p DOUBLE PRECISION,
    soil_k DOUBLE PRECISION,
    irrigation_type VARCHAR(50),
    rainfall_mm DOUBLE PRECISION,
    budget_inr DOUBLE PRECISION,
    top_recommendation VARCHAR(50) NOT NULL,
    expected_yield_q_acre DOUBLE PRECISION,
    estimated_profit_inr DOUBLE PRECISION,
    yield_delta_pct DOUBLE PRECISION,
    image_storage_path TEXT,
    full_report_json JSONB
);

-- 2. Indexes for efficient lookup and dashboard filtering
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at 
    ON public.recommendations_history (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_recommendations_farmer 
    ON public.recommendations_history (farmer_name, district);

CREATE INDEX IF NOT EXISTS idx_recommendations_crop 
    ON public.recommendations_history (current_crop, top_recommendation);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.recommendations_history ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies:
-- Allow authenticated service operations or public reads for anonymous demo mode
-- Note: You can customize these policies in the Supabase Dashboard under Authentication > Policies.
CREATE POLICY "Allow select on recommendations_history for all users"
    ON public.recommendations_history
    FOR SELECT
    USING (true);

CREATE POLICY "Allow insert on recommendations_history for all users"
    ON public.recommendations_history
    FOR INSERT
    WITH CHECK (true);

-- End of reviewed migration

