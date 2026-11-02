# Retail Sales Prediction and Analysis
### End-to-End Enterprise Data Science, Relational Database Engineering & Predictive Machine Learning

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-orange.svg)](https://www.sqlite.org/)
[![ML](https://img.shields.io/badge/Model-Random%20Forest%20Regressor-brightgreen.svg)](https://scikit-learn.org/)
[![BI](https://img.shields.io/badge/BI-Power%20BI%20%7C%20Interactive%20Web-purple.svg)](https://powerbi.microsoft.com/)

---

Required commands:
Local Host: http://localhost:8001
To start the dashboard and open localhost:
"python -m http.server 8001 --directory .\dashboard"

To open in jyupyter notebook
"python -m notebook --ip=127.0.0.1 --port=8889 --ServerApp.root_dir="$PWD" .\notebooks\Retail_Sales_Analysis.ipynb"


## 1. Project Overview & Business Problem

Retail organizations operate across diverse omnichannel touchpoints (physical stores, mobile applications, and e-commerce websites) across multiple regional markets. Accurate understanding of historical sales trajectories, customer engagement behaviors, and reliable transaction-level order value forecasting is essential for:
- Optimizing warehouse stocking and safety stock buffers.
- Aligning marketing spend with high-yield festive demand surges (e.g., Diwali in Q4).
- Enhancing loyalty program monetization and omnichannel customer retention.

This project delivers a production-grade, reproducible data science solution implementing the **4-Stage Common Project Architecture** specified in the curriculum synopsis:
1. **Stage 1: SQL – Data Management** (Normalized Relational Schema, Table Constraints, DDL, Seed Data, Analytical Window Queries).
2. **Stage 2: Python – Data Processing & EDA** (Data hygiene, automated validation, statistical profiling, and publication-grade visualizations).
3. **Stage 3: Feature Engineering & Machine Learning** (Leak-free feature extraction, supervised regression benchmarking, hyperparameter-tuned `RandomForestRegressor`, evaluation using MAE, MSE, RMSE, and $R^2$).
4. **Stage 4: Power BI & Business Intelligence** (Star Schema dimensional modeling, 23+ DAX measures, interactive executive web dashboard application).

---

## 2. Project Directory Structure

```
retail_sales_project/
├── data/
│   ├── retail_sales_clean.csv             # 7,000 raw transaction records (2022–2025)
│   ├── retail_sales.db                    # Normalized SQLite relational database
│   └── test_predictions.csv              # Actual vs Predicted sales for 1,400 test records
├── sql/
│   ├── 01_schema.sql                      # DDL for dimensions, facts, indexes, and analytical view
│   ├── 02_seed_data.sql                   # Sample SQL insertion script for MySQL/SQLite portability
│   └── 03_analytical_queries.sql          # 10 advanced queries with window functions & CTEs
├── src/
│   ├── setup_database.py                  # Ingests CSV, constructs relational schema, populates DB
│   ├── run_sql_analysis.py                # Executes SQL analytical queries and outputs reports
│   ├── eda_and_processing.py              # Data cleaning, statistics, and generates 8 EDA charts
│   ├── train_predict.py                   # Feature engineering, model benchmarking & evaluation
│   ├── build_dashboard_data.py            # Generates JSON data payload for web dashboard
│   └── generate_notebook.py               # Generates the reproducible Jupyter Notebook
├── models/
│   └── retail_sales_rf_model.joblib       # Serialized Scikit-Learn Random Forest Pipeline
├── notebooks/
│   └── Retail_Sales_Analysis.ipynb         # Comprehensive end-to-end Jupyter Notebook
├── reports/
│   ├── figures/                           # 10 high-resolution analytical and diagnostic plots
│   │   ├── 01_category_revenue_and_orders.png
│   │   ├── 02_monthly_sales_trend_and_seasonality.png
│   │   ├── 03_channel_performance_and_basket.png
│   │   ├── 04_city_sales_distribution.png
│   │   ├── 05_loyalty_tier_comparison.png
│   │   ├── 06_customer_engagement_matrix.png
│   │   ├── 07_correlation_heatmap.png
│   │   ├── 08_order_value_distribution.png
│   │   ├── 09_rf_feature_importance.png
│   │   └── 10_actual_vs_predicted_sales.png
│   ├── model_evaluation_metrics.md        # Benchmark metrics table
│   └── sql_analysis_results.md            # Formatted analytical query outputs
├── power_bi/
│   └── DAX_Measures_and_Model_Guide.md    # Star Schema guide, 23+ DAX formulas & wireframes
└── dashboard/
    ├── index.html                         # Interactive executive web dashboard (Tailwind + Chart.js)
    └── dashboard_data.js                  # Embedded transaction and prediction payload
```

---

## 3. Stage-by-Stage Implementation & Technical Findings

### Stage 1: SQL Data Management
- Structured into normalized **Star Schema**:
  - `dim_categories`, `dim_products`, `dim_channels`, `dim_cities`, `dim_loyalty_tiers`, and `dim_customers`.
  - Transactional `fact_sales` table linked via foreign keys and indexed on `order_date`, `product_id`, `customer_id`, and `channel_id`.
- Formulated 10 production SQL queries using Window Functions (`DENSE_RANK() OVER (PARTITION BY ...)`), Lag Functions (`LAG()`), and CTEs to extract insights:
  - Ranked top products by category revenue.
  - Calculated Month-over-Month (MoM) growth showing recurrent Q4 Diwali surges (+30% to +70%).
  - Evaluated omnichannel channel shares and city-level customer penetration.

### Stage 2: Python Data Processing & Exploratory Data Analysis
- Dataset Profile: **7,000 orders**, 17 attributes spanning exactly 4 full calendar years (01-01-2022 to 31-12-2025). Zero missing values, zero duplicates.
- **Revenue Distribution:** Total 4-year gross merchandise value is **₹65,837,607.45 (₹6.58 Crores)** across 18 distinct products in 6 categories:
  - **Electronics:** ₹29.07M (44.2% share) – Smart TV (₹14.9M) and Smartphone (₹12.2M) drive highest gross sales.
  - **Fashion:** ₹19.88M (30.2% share) – High volume (1,711 transactions) led by Footwear and Ethnic Wear.
  - **Grocery, Sports, Home & Beauty:** ₹16.89M (25.6% combined share).
- **Omnichannel Breakdown:**
  - In-Store accounts for 43.9% of transactions (₹28.23M revenue).
  - Online & Mobile App drive 56.1% of transactions, commanding a higher AOV (₹9,825 Online vs. ₹9,182 In-Store).
- **Loyalty Program Economics:**
  - Non-Members: AOV ₹9,334 | Avg Annual Spend ₹63,892.
  - Platinum Members: AOV ₹9,663 | Avg Annual Spend ₹115,227 (**1.8x to 3.5x annual spend multiplier** + ₹999 annual subscription fee revenue).

### Stage 3: Feature Engineering & Machine Learning
- **Target Variable:** `Order_Value_INR` (Continuous Regression).
- **Leak-Free Guarantee:** `Annual_Spend_Est_INR` was identified as an arithmetic product of `Order_Value_INR * Orders_Per_Year`. Incorporating it would introduce fatal data leakage. It was strictly excluded from features.
- **Engineered Predictors:**
  - Temporal variables: `Order_Year`, `Order_Month`, `Order_Day`, `Day_Of_Week`, `Order_Quarter`, `Is_Weekend`, and `Is_Festive_Season` (Q4 flag).
  - Customer interaction ratios: `Logins_Per_Visit`, `Omnichannel_Index` (weighting digital logins and physical store visits).
  - One-Hot Categorical Encoding for products, categories, channels, and cities.
- **Benchmark Models Evaluated (80/20 Train-Test Split, 5,600 Train / 1,400 Test):**

| Model | Train MAE (₹) | Test MAE (₹) | Train RMSE (₹) | Test RMSE (₹) | Train $R^2$ | **Test $R^2$** |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Dummy Regressor (Mean)** | ₹7,893.28 | ₹7,932.87 | ₹12,232.00 | ₹12,361.50 | 0.0000 | -0.0000 |
| **Linear Regression** | ₹3,123.43 | ₹3,233.34 | ₹5,082.69 | ₹5,300.06 | 0.8273 | 0.8162 |
| **Ridge Regression ($\alpha=1.0$)** | ₹3,122.98 | ₹3,233.04 | ₹5,082.75 | ₹5,300.90 | 0.8273 | 0.8161 |
| **Decision Tree Regressor** | ₹1,303.21 | ₹3,691.37 | ₹2,601.34 | ₹6,831.18 | 0.9548 | 0.6946 |
| **Random Forest Regressor (Tuned)** | **₹1,393.29** | **₹3,053.70** | **₹2,305.20** | **₹5,273.10** | **0.9645** | **0.8180** |

- **Champion Model:** Tuned `RandomForestRegressor` achieves **$R^2 = 0.8180$** (explains 81.8% of test variance) with an average prediction error of only ₹3,053.70 on ticket sizes up to ₹70,000.
- **Feature Importance:** Category Electronics (44.2%), Product Headphones (22.7%), Category Fashion (7.0%), Product Smart TV (3.8%), and Avg Basket Items (3.0%) are the top 5 predictive determinants.

### Stage 4: Power BI & Business Intelligence
- Comprehensive Power BI guide provided in `power_bi/DAX_Measures_and_Model_Guide.md` with:
  - 23 verified DAX measures covering volume, financial KPIs, time intelligence (MoM, YoY, YTD), customer behavior, and forecast variance.
  - Multi-page report layout wireframes: Executive Summary, Product Performance, Omnichannel Intelligence, and ML Forecast Variance.
- Standalone interactive executive web dashboard implemented in `dashboard/index.html`:
  - Instant client-side filtering across Fiscal Years (2022-2025), Categories, Channels, and Cities.
  - Live recalculation of Gross Revenue, Orders, AOV, Membership Fees, and Return Rates.
  - 6 interactive Chart.js visualizations + embedded **What-If Order Value & Revenue Estimator Simulator**.

---

## 4. How to Run the Project

### Prerequisites
- Python 3.10+ with `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `joblib`, and `tabulate`.
- Any modern web browser (Chrome, Edge, Firefox) for the dashboard.

### Step 1: Initialize Database & Run SQL Stage
```bash
python src/setup_database.py
python src/run_sql_analysis.py
```

### Step 2: Run Exploratory Data Analysis (EDA)
```bash
python src/eda_and_processing.py
```
*Generates 8 high-resolution figures in `reports/figures/`.*

### Step 3: Train Machine Learning Pipeline & Evaluate
```bash
python src/train_predict.py
```
*Outputs evaluation metrics, saves `models/retail_sales_rf_model.joblib`, and creates `data/test_predictions.csv`.*

### Step 4: Open the Interactive Executive Dashboard
Live dashboard: https://sparklemihika.github.io/retail-sales-analysis-and-prediction-project/

Simply open the file in your browser:
```
retail_sales_project/dashboard/index.html
```
Or start a local web server:
```bash
python -m http.server 8000 --directory dashboard
# Open http://localhost:8000 in your browser
```
The dashboard is also configured for automatic deployment to GitHub Pages. After pushing this repository's `main` branch to GitHub, the workflow in `.github/workflows/deploy-pages.yml` publishes the contents of `dashboard/`. Find the live URL under **Settings → Pages** or in the completed workflow deployment.

### Step 5: Launch the Jupyter Notebook
```bash
jupyter notebook notebooks/Retail_Sales_Analysis.ipynb
```

---

## 5. Strategic Retail Recommendations

1. **Pre-Festive Inventory Staging (August - September):**
   - October and November capture up to 35% of annual electronics and apparel demand due to Diwali festivities. Supply chains must stage inventory 45-60 days prior to Q4 to prevent out-of-stock lost revenue.
2. **Drive Digital Channel Adoption for Higher Ticket Sizes:**
   - Online orders exhibit an AOV of ₹9,825 compared to ₹9,182 for In-Store. Promoting the mobile app through exclusive in-app bundle discounts will increase average order values.
3. **Upgrade Silver Members to Platinum Tier:**
   - Platinum tier customers generate 1.8x higher annual spend and provide ₹999 recurring fee revenue with near-zero churn. Introducing tiered milestone rewards will accelerate loyalty tier upgrades.
