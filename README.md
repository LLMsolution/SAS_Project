# SAS Material Supply Analysis Dashboard

Streamlit dashboard for analyzing and predicting material preload requirements for aircraft C-checks at SAS.

## Features

### 1. Overview & KPIs (Homepage)
- High-level summary statistics and KPIs
- C-checks by aircraft type and check type
- Timeline trends and station performance
- Data quality and completeness metrics

### 2. C-Check Analysis
- Detailed analysis of individual C-checks
- Planned vs consumed material comparison
- Material list tables (planned and consumed)
- Top 10 parts by cost
- Planning accuracy and variance analysis

### 3. Material Prediction (ML Model)
- Predict material requirements for future C-checks
- Random Forest model trained on 46 C-checks with consumption data
- Hybrid prediction approach (ML + fallback to planned material)
- Similar historical C-checks recommendation
- Confidence scores and prediction ranges
- Feature importance visualization

### 4. Trend Analysis
- Planning accuracy trends over time
- Cost trends (overall and by aircraft type)
- Material usage trends with min/max ranges
- Station performance comparison
- Check type comparison (2-year, 4-year, 6-year)

### 5. Aircraft Insights
- Aircraft type-specific analysis
- Utilization correlation analysis (hours, cycles vs parts/cost)
- Top parts by aircraft type
- Cost distribution analysis
- Cross-aircraft type comparison

## Running the Dashboard

### Start Dashboard
```bash
cd "C:\Users\jesse\Documents\Aviation Opleiding\SAS_Project"
python3 -m streamlit run app.py
```

The dashboard will be available at:
- Local URL: http://localhost:8501
- Network URL: http://192.168.1.81:8501

### Stop Dashboard
Press `Ctrl+C` in the terminal where Streamlit is running.

## Data Requirements

The dashboard expects the following Excel files in the project root:
- `maintenance_workpacks_final_clean.xlsx` (267 rows, 254 C-checks)
- `aircraft_utilization.xlsx` (4686 rows)
- `material_consumption.xlsx` (4134 rows)
- `planned_material_on_workpacks.xlsx` (114,012 rows)

## Key Insights

- **Total C-Checks Analyzed:** 254
- **C-Checks with Consumption Data:** 46 (18.1%)
- **C-Checks with Planned Data:** 197 (77.5%)
- **Average Cost per C-Check:** €1,270,277

## ML Model Details

**Model Type:** Random Forest Regressor
- **Training Samples:** 46 C-checks with actual consumption data
- **Features Used:**
  - Aircraft type
  - Aircraft hours and cycles
  - Check type (2Y, 4Y, 6Y)
  - End of lease (EOL) flag
  - Station
  - Duration
  - Planned parts count and cost

**Prediction Strategy:**
1. Primary: ML model prediction with confidence score
2. Fallback: Adjusted planned material (historical accuracy factor)
3. Last resort: Historical average from training data

## SAS Branding

The dashboard uses official SAS corporate branding:
- **Primary Color:** #2B3087 (SAS Blue)
- **Secondary Color:** Black
- **Logo:** Scandinavian Airlines logo displayed in sidebar
- **Font:** Sans serif (closest to Rotis Semi Serif)
- **Design:** No emoji characters, professional aviation aesthetic

## Navigation

Use the sidebar to:
- Navigate between different analysis pages
- Apply filters (aircraft type, check type, station, date range)
- Input data for material prediction
- Select specific C-checks for detailed analysis

## Technical Stack

- **Frontend:** Streamlit
- **Data Processing:** Pandas, NumPy
- **Machine Learning:** scikit-learn (Random Forest)
- **Visualization:** Plotly
- **Excel I/O:** openpyxl

## Project Structure

```
SAS_Project/
├── app.py                          # Main entry point
├── .streamlit/
│   └── config.toml                 # SAS branding theme
├── assets/
│   └── Scandinavian_Airlines_logo.svg.png
├── pages/
│   ├── 1_Overview.py
│   ├── 2_C-Check_Analysis.py
│   ├── 3_Material_Prediction.py
│   ├── 4_Trend_Analysis.py
│   └── 5_Aircraft_Insights.py
├── utils/
│   ├── data_loader.py              # Data loading with caching
│   ├── feature_engineering.py      # ML feature creation
│   └── ml_model.py                 # Random Forest predictor
├── models/
│   └── material_predictor.pkl      # Saved trained model
└── data files (xlsx)
```

## Data Caching

The dashboard uses Streamlit's caching mechanisms for optimal performance:
- `@st.cache_data` for data loading (refreshed per session)
- `@st.cache_resource` for ML model (loaded once)

## Support

For issues or questions, contact the project team at Amsterdam University of Applied Sciences.

**Project:** Analysis of Material Supply Processes for Heavy Aircraft Maintenance

---

Dashboard developed for SAS Scandinavian Airlines
