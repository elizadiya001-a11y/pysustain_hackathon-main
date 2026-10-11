# 🌾 FASAL AI — Intelligent Crop Recommendation & Farm Digital Twin

**PySustain Hackathon** · *Track: Intelligent Solutions for Sustainable Agriculture*  
**Team FASAL:** Gargi Bhojkar, Srijon Sarkar, Shansita Padhi, Diya Elizabeth Reji (BACSE101)

---

## 📌 1. Project Overview & Architecture

**FASAL AI** is an explainable agricultural decision-support web application and digital farm twin tailored for smallholder farmers and agricultural extension officers in groundwater-stressed Indian agricultural regions.

In districts where policy has driven water-intensive monocultures (e.g. continuous paddy and wheat), aquifers are rapidly depleting. Farmers and extension officers lack low-cost, low-risk tools to simulate:
> *"What if we switch from flood-irrigated wheat to drip-irrigated maize, cotton, or a pulse rotation like chickpea or moong dal?"*

### Architecture & Data Flow

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FASAL AI USER INTERFACE                         │
│   Streamlit Web App (9 Responsive Mobile-First & Desktop Pages)        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     APPLICATION LOGIC LAYER (src/)                     │
│  ┌─────────────────────────┐         ┌───────────────────────────────┐ │
│  │ data_loader.py          │         │ data_cleaning.py              │ │
│  │ Unified dataset joins   │         │ Outliers, units, missingness  │ │
│  └───────────┬─────────────┘         └──────────────┬────────────────┘ │
│              │                                      │                  │
│              ▼                                      ▼                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ AI & MACHINE LEARNING PIPELINE                                  │   │
│  │ • MobileNetV3 Soil Classifier (6 Classes, PyTorch)              │   │
│  │ • Random Forest Crop Suitability (Scikit-Learn vs Baseline)     │   │
│  │ • Agronomic Yield Predictor (80% Prediction Intervals & SHAP)   │   │
│  │ • Groundwater Pumping Energy Physics: E = (ρ·g·V·H)/(3.6e6·η)   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│              │                                      │                  │
│              ▼                                      ▼                  │
│  ┌─────────────────────────┐         ┌───────────────────────────────┐ │
│  │ crop_comparison.py      │         │ reporting.py                  │ │
│  │ Side-by-side economics  │         │ Executive report, CSV export  │ │
│  └─────────────────────────┘         └───────────────────────────────┘ │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 SUPABASE POSTGRESQL & STORAGE BACKEND                  │
│  • farms (250 digitized parcels across 8 agro-climatic districts)     │
│  • soil (pH, organic carbon, NPK, texture, soil groups)                │
│  • weather (1,750 temperature, rainfall & humidity records)            │
│  • market_prices (MSP, wholesale prices, water requirements)           │
│  • satellite_data (Sentinel-2 NDVI, NDMI, BSI & SoilGrids topsoil)     │
│  • soil_types (visual characteristics & hand ribbon tests)             │
│  • recommendations_history (secure cloud persistence with RLS)         │
│  • Storage Bucket: field-uploads (secure farmer photo storage)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 2. File & Directory Structure

```text
pysustain_hackathon-main/
│
├── .env                              # Supabase API URL and Secret credentials (gitignored)
├── .env.example                      # Template with placeholder credentials
├── .gitignore                        # Git ignore file protecting .env and virtual environments
├── requirements.txt                  # Python dependencies
├── README.md                         # Complete project documentation
├── train_models.py                   # Reproducible model training & evaluation script
├── app.py                            # Streamlit entry point with 9 responsive views
│
├── src/                              # Clean Modular Architecture
│   ├── __init__.py
│   ├── supabase_client.py            # Official Supabase Python SDK client, queries, RLS, storage
│   ├── data_loader.py                # Dataset joining (farms + soil + weather + satellite)
│   ├── data_cleaning.py              # Unit conversions (acres/ha/bigha), imputation & audits
│   ├── image_analysis.py             # MobileNetV3 PyTorch visual soil inference & disclaimers
│   ├── soil_analysis.py              # ICAR nutrient diagnostics & soil amendments
│   ├── crop_recommendation.py        # Random Forest suitability, water cap & net margin rank
│   ├── yield_prediction.py           # Multi-factor yield regressor with 80% confidence interval
│   ├── crop_comparison.py            # Side-by-side yield, profit delta & resource trade-offs
│   └── reporting.py                  # Farmer advisory report generator (Text/Markdown & CSV)
│
├── core/                             # Foundational Agronomic & Physics Engines
│   ├── config.py                     # Agronomic envelopes, crop parameters, irrigation constants
│   ├── db.py                         # Direct SQL access & offline fallback generator
│   ├── models.py                     # Non-linear Mitscherlich-Baule yield response surface
│   ├── simulation.py                 # Pumping energy physics & economic balance
│   ├── recommender.py                # Water-capped profit recommender
│   ├── sustainability.py             # 5-Pillar ESG sustainability scorecard (0-100)
│   ├── advisory.py                   # Feature phone SMS generator (<= 160 chars in EN & HI)
│   └── persistence.py                # Scenario state persistence and duplication
│
├── views/                            # 9 Modular UI Screens
│   ├── home_dashboard.py             # Home Dashboard: KPIs, cloud status, parcel selector
│   ├── farm_assessment.py            # Farm Assessment: Survey, photo upload, satellite chip
│   ├── soil_analysis_view.py         # Soil Analysis: ICAR nutrient card, visual model, ribbon guide
│   ├── crop_recommendations_view.py  # Crop Recommendations: Ranked crops, water cap, report download
│   ├── current_crop_comparison_view.py# Current Crop Comparison: Side-by-side yield & profit delta
│   ├── digital_twin_view.py          # Farm Digital Twin: Interactive levers, pump physics & SMS
│   ├── dataset_explorer_view.py      # Dataset Explorer: Safe table schemas & missingness audit
│   ├── model_performance_view.py     # Model Performance: Benchmarks vs baselines & limitations
│   └── recommendation_history_view.py# Recommendation History: Supabase history & CSV export
│
├── models/                           # Trained Model Weights & Metadata
│   ├── soil_classifier.pt            # Trained PyTorch MobileNetV3 weights (6 soil classes)
│   ├── soil_classifier_metadata.json # Architecture, validation accuracy (71.4%), class labels
│   ├── crop_suitability_rf.joblib    # Scikit-learn Random Forest Pipeline (88.2% accuracy)
│   ├── crop_suitability_metadata.json# F1-score, feature importances, baseline comparisons
│   └── yield_model_metrics.json      # RMSE (0.93 q/ac vs 73.1 baseline), 80% CI calibration
│
├── sql/
│   └── reviewed_migrations.sql       # Reviewed SQL migration for recommendations_history with RLS
│
├── tests/
│   ├── test_fasal.py                 # 9 End-to-end tests: Supabase, models, inputs, reporting
│   └── test_all.py                   # 9 Unit tests: Physics, energy, SMS, sustainability
│
└── static/
    └── style.css                     # Mobile-first and desktop agricultural stylesheet
```

---

## ⚡ 3. Supabase Cloud Integration

### Project Details
- **Dashboard URL:** `https://supabase.com/dashboard/project/bwlopgkkaasgmkdkoayb`
- **REST API Endpoint:** `https://bwlopgkkaasgmkdkoayb.supabase.co`

### Schema Overview
1. `farms` (250 rows): `farm_id`, `farmer_name`, `area_acres`, `current_crop`, `sowing_date`, `latitude`, `longitude`, `district`, `state`.
2. `soil` (250 rows): `farm_id`, `ph`, `organic_carbon`, `nitrogen_kg_ha`, `phosphorus_kg_ha`, `potassium_kg_ha`, `texture`, `soil_group`.
3. `weather` (1,750 rows): `farm_id`, `date`, `temp_max_c`, `temp_min_c`, `rainfall_mm`, `humidity_pct`.
4. `market_prices` (8 rows): `crop_name`, `msp_per_quintal`, `market_price_per_quintal`, `water_req_liters_per_acre`.
5. `satellite_data` (250 rows): `farm_id`, `window_start`, `window_end`, `n_scenes`, `ndvi_real`, `ndmi_real`, `bsi_real`, `sand_pct`, `clay_pct`, `silt_pct`, `ph_soilgrids`, `soc_g_per_kg`, `texture_usda`, `image_path`, `image_url`.
6. `soil_types` (5 rows): `soil_type`, `description`, `hand_test`, `image_path`, `image_url`.
7. `recommendations_history` (New review migration): Persists farmer submissions, recommendations, and reports with Row Level Security.
8. `Storage Bucket (field-uploads)`: Secure storage bucket for farmer field photos.

---

## 🛠️ 4. Setup, Installation & Execution Commands

### Prerequisites
- Python 3.10+ (Windows 64-bit)
- Windows PowerShell in VS Code

### Step 1: Environment Variables
Create or verify your `.env` file in the project root:
```ini
SUPABASE_URL=https://bwlopgkkaasgmkdkoayb.supabase.co
SUPABASE_KEY=your_supabase_secret_key
SUPABASE_STORAGE_BUCKET=field-uploads
```

### Step 2: Install Dependencies
In PowerShell:
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Run Database Inspection
To verify live Supabase connectivity and table counts:
```powershell
python -c "from src.supabase_client import check_connection_health; print(check_connection_health())"
```

### Step 4: Train & Validate Models (Reproducible Pipeline)
To train the MobileNetV3 visual soil classifier, Random Forest crop suitability model, and validate yield metrics:
```powershell
python train_models.py
```
*Expected Output:*
- Soil Model Validation Accuracy: `71.4%` (MobileNetV3)
- Crop Suitability Accuracy: `88.2%` (vs `12.5%` Baseline)
- Yield Regressor RMSE: `0.93 q/acre` (98.7% improvement over baseline)
- Models saved directly to `models/`

### Step 5: Run Automated Tests
Execute the complete test suites (18 tests total):
```powershell
# Run FASAL AI integration tests:
python -m unittest tests/test_fasal.py

# Run foundational physics and agronomy tests:
python -m unittest tests/test_all.py
```

### Step 6: Launch the Streamlit Web Application
```powershell
python -m streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 📲 5. Hackathon Mobile Demo over Wi-Fi
To demonstrate the mobile-first portrait view live on an Android device:
1. Connect laptop and Android phone to the same Wi-Fi network.
2. Find your laptop IP using `ipconfig` in PowerShell (e.g., `192.168.1.15`).
3. Launch Streamlit bound to all interfaces:
   ```powershell
   python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
   ```
4. On your Android phone browser, open: `http://<YOUR_LAPTOP_IP>:8501`

---

## 🏆 6. Scientific Validation & Model Benchmarks

| Objective | Benchmark / Baseline | FASAL Result | Status |
| :--- | :--- | :--- | :---: |
| **O1 / G2: Yield Model** | Historical Mean Baseline RMSE: 73.1 q/ac | **Held-out RMSE: 0.93 q/ac (98.7% improvement)** | ✅ Exceeded |
| **O2 / G3: Uncertainty** | Nominal 80% Coverage | **Empirical 80% Coverage: 81.4% (±1.4%)** | ✅ Verified |
| **O3 / G4: Crop Recommender** | Dummy Baseline: 12.5% Accuracy | **Random Forest Accuracy: 88.2% (F1: 0.883)** | ✅ Superior |
| **O4 / G1: Soil Visual Model** | Random Guess: 16.7% (6 classes) | **MobileNetV3 Validation Accuracy: 71.4%** | ✅ Validated |
| **O5 / G1: Pumping Physics** | Groundwater Head Equation | **$E = 0.168\text{ kWh/m}^3$ at 40m head** | ✅ Validated |
| **O6 / G4: Sustainability** | UN SDG Alignment | **5-Pillar Scorecard (0–100) + Nitrogen Surplus** | ✅ Delivered |
| **O7 / G5: Advisory Delivery** | SMS $\le 160$ chars (English & Hindi) | **100% Compliant (112–148 chars)** | ✅ Tested |

---

## ⚠️ 7. Limitations & Ethical Disclaimers
1. **No Maximum Yield Guarantees:** All yield estimates are presented as expected agronomic potentials with calibrated 80% prediction intervals.
2. **Visual vs Chemical Soil Testing:** Ordinary RGB photography detects physical soil color and surface texture (e.g. Red, Black, Alluvial, Clay). It cannot measure exact NPK or pH chemistry; physical laboratory soil testing is recommended.
3. **Weight vs Economic Profit:** Sugarcane or cereal tonnage cannot be directly equated with pulse grain weights; comparisons are strictly made on net profit margin per acre.
