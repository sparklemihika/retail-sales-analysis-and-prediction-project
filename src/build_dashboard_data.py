import os
import json
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\LENOVO\.gemini\antigravity\scratch\retail_sales_project"
CSV_PATH = os.path.join(BASE_DIR, "data", "retail_sales_clean.csv")
TEST_PREDS_PATH = os.path.join(BASE_DIR, "data", "test_predictions.csv")
DASHBOARD_HTML_PATH = os.path.join(BASE_DIR, "dashboard", "index.html")

print("[INFO] Preparing interactive dashboard payload...")
df = pd.read_csv(CSV_PATH)
df['Parsed_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
df['Year'] = df['Parsed_Date'].dt.year
df['Month'] = df['Parsed_Date'].dt.month
df['Year_Month'] = df['Parsed_Date'].dt.strftime('%Y-%m')

test_preds = pd.read_csv(TEST_PREDS_PATH)

# Summary by Year, Category, Channel, City
records = []
for _, r in df.iterrows():
    records.append({
        'id': r['Order_ID'],
        'date': r['Order_Date'],
        'ym': r['Year_Month'],
        'year': int(r['Year']),
        'cat': r['Category'],
        'prod': r['Product'],
        'chan': r['Channel'],
        'city': r['City'],
        'tier': r['Loyalty_Tier'],
        'basket': int(r['Avg_Basket_Items']),
        'ret': int(r['Returns']),
        'rating': float(r['Customer_Rating']),
        'val': float(r['Order_Value_INR']),
        'mem': float(r['Membership_Revenue_INR']),
        'annual': float(r['Annual_Spend_Est_INR']),
        'visits': int(r['Monthly_Store_Visits']),
        'logins': int(r['App_Logins_Month'])
    })

# Sample 100 test predictions for scatter plot
scatter_sample = []
sample_df = test_preds.sample(n=min(120, len(test_preds)), random_state=42)
for _, r in sample_df.iterrows():
    scatter_sample.append({
        'actual': round(float(r['Actual_Order_Value_INR']), 2),
        'pred': round(float(r['Predicted_Order_Value_INR']), 2),
        'cat': r['Category'],
        'prod': r['Product']
    })

print(f"[INFO] Processed {len(records)} transaction records and {len(scatter_sample)} test prediction samples.")

# Write data to a json file in dashboard directory
data_json_path = os.path.join(BASE_DIR, "dashboard", "dashboard_data.js")
with open(data_json_path, "w", encoding="utf-8") as f:
    f.write(f"const RETAIL_TRANSACTIONS = {json.dumps(records)};\n")
    f.write(f"const ML_TEST_PREDICTIONS = {json.dumps(scatter_sample)};\n")

print(f"[SUCCESS] Exported payload to {data_json_path}")
