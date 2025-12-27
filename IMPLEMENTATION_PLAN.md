# SAS Material Preload Analysis - Streamlit Dashboard Implementation Plan

## Project Overview
Create an interactive Streamlit dashboard with ML model to analyze and predict material preload for aircraft C-checks at SAS.

**Goal:**
1. Provide insights into preload accuracy (planned vs consumed materials)
2. Predict material requirements for future C-checks
3. Help improve material planning and reduce costs/delays

## Datasets (No Master Dataset - Keep Separate)
- `maintenance_workpacks_final_clean.xlsx` (267 rows, 254 C-checks)
- `aircraft_utilization.xlsx` (4686 rows)
- `material_consumption.xlsx` (4134 rows, only 46 C-checks have data)
- `planned_material_on_workpacks.xlsx` (114,012 rows)

**Key Challenge:** Only 17.6% of C-checks have consumption data due to MRO-supplied materials not being tracked.

---

## Branding Requirements

### SAS Corporate Identity
- **Logo:** `Scandinavian_Airlines_logo.svg.png` (display in sidebar)
- **Primary Color:** #2B3087 (SAS Blue)
- **Secondary Color:** Black
- **Font:** Rotis Semi Serif
- **NO EMOJI:** Use text labels only, no emoji characters

### Streamlit Theming
```python
# .streamlit/config.toml
[theme]
primaryColor = "#2B3087"  # SAS Blue
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#000000"
font = "sans serif"  # Closest to Rotis Semi Serif
```

---

## Architecture Overview

### Data Flow
```
Raw Excel Files
    ↓
Data Loader Module (with caching)
    ↓
Feature Engineering Module
    ↓
├─→ ML Model (trained once, cached)
├─→ Dashboard Pages
└─→ Visualizations (Plotly)
```

### Streamlit App Structure (Multi-page)
```
app.py (main entry point)
├── pages/
│   ├── 1_Overview.py (Overview & KPIs)
│   ├── 2_C-Check_Analysis.py (Individual C-check analysis)
│   ├── 3_Material_Prediction.py (ML prediction for new C-check)
│   ├── 4_Trend_Analysis.py (Trends over time)
│   └── 5_Aircraft_Insights.py (Aircraft type analysis)
├── utils/
│   ├── data_loader.py (Load and cache datasets)
│   ├── feature_engineering.py (Create ML features)
│   ├── ml_model.py (Train and predict)
│   └── visualizations.py (Plotly charts)
└── models/
    └── material_predictor.pkl (Saved ML model)
```

---

## Implementation Plan

### Phase 1: Data Loading & Feature Engineering

**File: `utils/data_loader.py`**
```python
@st.cache_data
def load_workpacks():
    # Load maintenance_workpacks_final_clean.xlsx
    # Return clean dataframe

@st.cache_data
def load_utilization():
    # Load aircraft_utilization.xlsx
    # Return dataframe

@st.cache_data
def load_consumption():
    # Load material_consumption.xlsx
    # Aggregate by wpno_i

@st.cache_data
def load_planned_material():
    # Load planned_material_on_workpacks.xlsx
    # Aggregate by wpno_i

def get_master_view():
    # Join datasets on-demand
    # Return combined view with utilization + consumption + planned
```

**File: `utils/feature_engineering.py`**
```python
def create_ml_features(workpacks_df, utilization_df, consumption_df, planned_df):
    """
    Create features for ML model:

    Features to engineer:
    1. Aircraft features:
       - ac_typ (encoded)
       - aircraft_hours (from utilization)
       - aircraft_cycles (from utilization)
       - hours_per_cycle

    2. Check features:
       - check_type (2-year, 4-year, 6-year)
       - is_eol (0/1)
       - station (encoded)
       - workpack_duration_days

    3. Historical features (from planned material):
       - planned_parts_count
       - planned_cost_total
       - planned_qty_total

    4. Target variable (from consumption):
       - consumed_parts_count (main target)
       - consumed_cost_total (secondary target)

    Handle missing consumption data:
    - Use planned material as proxy when consumption missing
    - Flag rows with actual consumption vs imputed
    """
```

---

### Phase 2: ML Model Development

**File: `utils/ml_model.py`**

**Strategy for Limited Data:**
Since only 46/254 C-checks have consumption data, use hybrid approach:

1. **Primary Model:** Train on 46 C-checks with actual consumption
   - Target: `consumed_parts_count`, `consumed_cost_total`
   - Use cross-validation due to small sample size

2. **Fallback:** Use planned material statistics
   - For checks without historical consumption
   - Calculate average planning accuracy from the 46 known cases
   - Apply accuracy factor to planned material

3. **Model Type:** Random Forest Regressor
   - Good with small datasets
   - Handles non-linear relationships
   - Can identify feature importance

```python
class MaterialPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_cols = []

    def train(self, X_train, y_train):
        """Train Random Forest on available consumption data"""
        # Use RandomForestRegressor with cross-validation
        # Save model to models/material_predictor.pkl

    def predict(self, X_new):
        """Predict material needs for new C-check"""
        # Return predicted parts count and cost

    def predict_with_fallback(self, X_new, planned_data):
        """
        If model confidence is low, use planned material with adjustment factor
        """
```

**Features for ML Model:**
- `ac_typ` (aircraft type)
- `aircraft_hours`
- `aircraft_cycles`
- `check_type` (2Y, 4Y, 6Y)
- `is_eol` (end of lease)
- `station`
- `planned_parts_count`
- `planned_cost_total`

**Targets:**
- Primary: `consumed_parts_count`
- Secondary: `consumed_cost_total`

---

### Phase 3: Streamlit Dashboard Pages

#### Page 1: Overview & KPIs (`1_Overview.py`)
**Purpose:** High-level summary of C-check material planning

**Components:**
1. **KPI Cards (top row)**
   - Total C-checks analyzed
   - Average planning accuracy (planned vs consumed)
   - Total cost variance
   - Average parts per C-check

2. **Key Metrics**
   - C-checks with consumption data: 46/254 (18.1%)
   - C-checks with planned data: 197/254 (77.5%)
   - Average cost per C-check: €1,270,277

3. **Quick Filters (sidebar)**
   - Aircraft type
   - Check type (2Y, 4Y, 6Y)
   - Date range
   - Station

4. **Charts**
   - Bar chart: C-checks by aircraft type
   - Pie chart: Check type distribution
   - Line chart: C-checks over time

---

#### Page 2: C-Check Analysis (`2_C-Check_Analysis.py`)
**Purpose:** Detailed analysis of individual C-checks

**Components:**
1. **C-Check Selector**
   - Dropdown to select specific C-check (by wpno or ac_registr)

2. **C-Check Details Card**
   - Aircraft: registration, type, hours, cycles
   - Check: type, station, duration, dates
   - Status: is_eol, is_bridging_task

3. **Material Analysis (if consumption data available)**
   - Planned vs Consumed comparison table
   - Top 10 parts by cost
   - Variance analysis:
     * Parts count variance
     * Quantity variance
     * Cost variance
   - Planning accuracy score

4. **Visualizations**
   - Bar chart: Planned vs Consumed (parts count, cost)
   - Scatter plot: Part-level analysis (planned vs consumed per part)

5. **Material List Tables**
   - Planned materials table (with filters)
   - Consumed materials table (if available)

---

#### Page 3: Material Prediction (`3_Material_Prediction.py`)
**Purpose:** Predict material needs for a new C-check

**Components:**
1. **Input Form (sidebar)**
   - Aircraft registration (dropdown or text)
   - OR manual inputs:
     * Aircraft type
     * Aircraft hours
     * Aircraft cycles
   - Check type (2Y, 4Y, 6Y)
   - Station
   - Is EOL? (checkbox)

2. **Prediction Button**
   - "Predict Material Requirements"

3. **Prediction Results**
   - **Predicted Metrics:**
     * Parts count (with confidence interval)
     * Estimated cost (with range)
     * Estimated duration

   - **Model Info:**
     * Model type: Random Forest
     * Training data: 46 C-checks
     * Feature importance chart

   - **Recommended Material List**
     * Top N parts predicted (based on similar C-checks)
     * Part numbers, descriptions, estimated quantities
     * Priority ranking

4. **Similar Historical C-Checks**
   - Table showing 5 most similar historical C-checks
   - Used for recommendation logic

5. **Confidence Indicator**
   - Visual indicator of prediction confidence
   - Explanation of factors affecting confidence

---

#### Page 4: Trend Analysis (`4_Trend_Analysis.py`)
**Purpose:** Analyze trends over time

**Components:**
1. **Planning Accuracy Trends**
   - Line chart: Planning accuracy over time (monthly)
   - Shows improvement or degradation in planning

2. **Cost Trends**
   - Line chart: Average cost per C-check over time
   - Breakdown by aircraft type

3. **Material Usage Trends**
   - Line chart: Average parts per C-check over time
   - Identify seasonal patterns or changes

4. **Station Performance**
   - Bar chart: Planning accuracy by station
   - Table: Metrics per station

5. **Check Type Analysis**
   - Comparison: 2Y vs 4Y vs 6Y checks
   - Average duration, cost, parts count

---

#### Page 5: Aircraft Insights (`5_Aircraft_Insights.py`)
**Purpose:** Aircraft type-specific analysis

**Components:**
1. **Aircraft Type Selector**
   - Dropdown: A320S, A330, A340, A350, E190

2. **Aircraft Type Summary**
   - Total C-checks for this type
   - Average utilization (hours, cycles)
   - Average material cost

3. **Utilization Correlation Analysis**
   - Scatter plot: Aircraft hours vs parts consumed
   - Scatter plot: Aircraft cycles vs cost
   - Correlation coefficients

4. **Parts Analysis by Aircraft Type**
   - Top 10 most used parts
   - Cost distribution
   - Typical material profile

5. **Comparison Table**
   - Compare all aircraft types side-by-side
   - Metrics: avg cost, avg parts, avg duration

---

## File Structure

```
SAS_Project/
├── app.py                          # Main Streamlit entry point
├── .streamlit/
│   └── config.toml                 # SAS branding theme
├── assets/
│   └── Scandinavian_Airlines_logo.svg.png  # SAS logo
├── pages/
│   ├── 1_Overview.py
│   ├── 2_C-Check_Analysis.py
│   ├── 3_Material_Prediction.py
│   ├── 4_Trend_Analysis.py
│   └── 5_Aircraft_Insights.py
├── utils/
│   ├── __init__.py
│   ├── data_loader.py              # Load and cache datasets
│   ├── feature_engineering.py      # Create ML features
│   ├── ml_model.py                 # Train and predict
│   └── visualizations.py           # Reusable Plotly charts
├── models/
│   └── material_predictor.pkl      # Saved trained model
├── data/                           # Excel files (existing)
│   ├── maintenance_workpacks_final_clean.xlsx
│   ├── aircraft_utilization.xlsx
│   ├── material_consumption.xlsx
│   └── planned_material_on_workpacks.xlsx
└── requirements.txt                # Python dependencies
```

---

## Implementation Steps

### Step 1: Setup (20 min)
1. Create folder structure (including .streamlit/ and assets/)
2. Copy SAS logo to `assets/Scandinavian_Airlines_logo.svg.png`
3. Create `.streamlit/config.toml` with SAS branding
4. Create `requirements.txt`:
   ```
   streamlit
   pandas
   numpy
   scikit-learn
   plotly
   openpyxl
   ```
3. Install: `pip install -r requirements.txt`

### Step 2: Data Loading Module (1 hour)
1. Create `utils/data_loader.py`
2. Implement cached loading functions for all 4 datasets
3. Implement `get_master_view()` for on-demand joining
4. Test data loading in notebook

### Step 3: Feature Engineering (1 hour)
1. Create `utils/feature_engineering.py`
2. Implement feature creation
3. Handle missing values
4. Test feature generation

### Step 4: ML Model (2 hours)
1. Create `utils/ml_model.py`
2. Train model on 46 C-checks with consumption data
3. Evaluate with cross-validation
4. Save model to `models/material_predictor.pkl`
5. Implement prediction function with fallback

### Step 5: Main App Structure (30 min)
1. Create `app.py` with sidebar navigation
2. Set page config, title, SAS logo in sidebar
3. Add SAS branding (colors #2B3087, black)
4. Add introduction and data summary
5. Ensure NO EMOJI characters anywhere

### Step 6: Dashboard Pages (4-5 hours)
Implement each page sequentially:
1. Overview page (1 hour)
2. C-Check Analysis page (1 hour)
3. Material Prediction page (1.5 hours) - most complex
4. Trend Analysis page (1 hour)
5. Aircraft Insights page (1 hour)

### Step 7: Visualizations Module (1 hour)
1. Create `utils/visualizations.py`
2. Create reusable Plotly chart functions
3. Standardize colors, themes

### Step 8: Testing & Refinement (1-2 hours)
1. Test all features
2. Handle edge cases
3. Add error handling
4. Improve UX

---

## Key Design Decisions

### 1. Why Keep Datasets Separate?
- **Pro:** More flexible, easier to update individual datasets
- **Pro:** Lower memory footprint (load on-demand)
- **Con:** Slightly more complex joins
- **Decision:** Keep separate, use caching for performance

### 2. ML Model Strategy (Limited Data)
- **Challenge:** Only 46 C-checks with consumption data
- **Solution:**
  * Train model on 46 samples
  * Use cross-validation for robustness
  * Provide confidence scores
  * Fallback to adjusted planned material
  * Show similar historical cases for transparency

### 3. Visualization Library
- **Choice:** Plotly
- **Why:** Interactive, professional, works well with Streamlit

### 4. Caching Strategy
- Use `@st.cache_data` for data loading (refresh every session)
- Use `@st.cache_resource` for ML model (load once)

---

## Handling the Limited Consumption Data Challenge

**Problem:** Only 46/254 C-checks (18.1%) have actual consumption data.

**Solutions Implemented:**

1. **Model Approach:**
   - Train on available 46 samples
   - Use robust cross-validation
   - Report confidence levels

2. **Hybrid Prediction:**
   - Use ML model when confident
   - Fall back to adjusted planned material
   - Show uncertainty ranges

3. **Recommendation System:**
   - Find similar historical C-checks
   - Show actual consumption from similar cases
   - Provide material list based on patterns

4. **Transparency:**
   - Always show data availability
   - Explain prediction confidence
   - Display similar cases used

5. **Focus on Planned Material Analysis:**
   - Even without consumption data, analyze planned material
   - Show planning patterns
   - Identify improvement opportunities

---

## Success Metrics

Dashboard is successful if it enables users to:
1. ✅ Understand historical planning accuracy
2. ✅ Predict material needs for new C-checks
3. ✅ Identify trends and improvement opportunities
4. ✅ Compare aircraft types and stations
5. ✅ Make data-driven decisions on material preload

---

## Timeline Estimate

- **Total:** 12-15 hours for full implementation
- **MVP (Pages 1-3):** 6-8 hours
- **Full Version (All 5 pages):** 12-15 hours

---

## Next Steps After Plan Approval

1. Create folder structure
2. Install dependencies
3. Start with data_loader.py
4. Build ML model
5. Create main app.py
6. Implement pages one by one
7. Test and refine
