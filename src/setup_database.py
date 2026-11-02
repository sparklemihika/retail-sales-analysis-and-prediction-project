import os
import sqlite3
import pandas as pd
import numpy as np

# Define Paths
BASE_DIR = r"C:\Users\LENOVO\.gemini\antigravity\scratch\retail_sales_project"
CSV_PATH = os.path.join(BASE_DIR, "data", "retail_sales_clean.csv")
DB_PATH = os.path.join(BASE_DIR, "data", "retail_sales.db")
SEED_SQL_PATH = os.path.join(BASE_DIR, "sql", "02_seed_data.sql")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

print("[INFO] Loading raw cleaned retail dataset...")
df = pd.read_csv(CSV_PATH)
df['Parsed_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
df['Formatted_Date'] = df['Parsed_Date'].dt.strftime('%Y-%m-%d')

print(f"[INFO] Total records loaded: {len(df)}")

# Remove existing database if present for a clean build
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Create Tables
print("[INFO] Creating normalized database schema in SQLite...")
cursor.executescript("""
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_categories;
DROP TABLE IF EXISTS dim_channels;
DROP TABLE IF EXISTS dim_cities;
DROP TABLE IF EXISTS dim_loyalty_tiers;

CREATE TABLE dim_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL UNIQUE,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES dim_categories (category_id)
);

CREATE TABLE dim_channels (
    channel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_cities (
    city_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL UNIQUE,
    region TEXT NOT NULL
);

CREATE TABLE dim_loyalty_tiers (
    tier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tier_name TEXT NOT NULL UNIQUE,
    annual_fee_inr REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE dim_customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT UNIQUE,
    city_id INTEGER NOT NULL,
    tier_id INTEGER NOT NULL,
    tenure_years INTEGER NOT NULL,
    monthly_store_visits INTEGER NOT NULL,
    app_logins_month INTEGER NOT NULL,
    orders_per_year INTEGER NOT NULL,
    FOREIGN KEY (city_id) REFERENCES dim_cities (city_id),
    FOREIGN KEY (tier_id) REFERENCES dim_loyalty_tiers (tier_id)
);

CREATE TABLE fact_sales (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL UNIQUE,
    order_date TEXT NOT NULL,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    basket_items INTEGER NOT NULL,
    returns_flag INTEGER NOT NULL,
    customer_rating REAL NOT NULL,
    order_value_inr REAL NOT NULL,
    membership_revenue_inr REAL NOT NULL,
    annual_spend_est_inr REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id),
    FOREIGN KEY (product_id) REFERENCES dim_products (product_id),
    FOREIGN KEY (channel_id) REFERENCES dim_channels (channel_id)
);
""")

# 2. Populate Dimensions
print("[INFO] Populating Dimensions...")

# Categories
categories = sorted(df['Category'].unique().tolist())
for cat in categories:
    cursor.execute("INSERT INTO dim_categories (category_name) VALUES (?)", (cat,))
conn.commit()

# Category mapping
cat_map = {row[1]: row[0] for row in cursor.execute("SELECT category_id, category_name FROM dim_categories").fetchall()}

# Products
prod_cat_pairs = df[['Product', 'Category']].drop_duplicates().sort_values('Product')
for _, row in prod_cat_pairs.iterrows():
    cursor.execute(
        "INSERT INTO dim_products (product_name, category_id) VALUES (?, ?)", 
        (row['Product'], cat_map[row['Category']])
    )
conn.commit()
prod_map = {row[1]: row[0] for row in cursor.execute("SELECT product_id, product_name FROM dim_products").fetchall()}

# Channels
channels = sorted(df['Channel'].unique().tolist())
for ch in channels:
    cursor.execute("INSERT INTO dim_channels (channel_name) VALUES (?)", (ch,))
conn.commit()
ch_map = {row[1]: row[0] for row in cursor.execute("SELECT channel_id, channel_name FROM dim_channels").fetchall()}

# City regions mapping (Standard Indian Retail Zones)
city_regions = {
    'Mumbai': 'West', 'Pune': 'West', 'Ahmedabad': 'West',
    'Delhi': 'North', 'Jaipur': 'North', 'Lucknow': 'North',
    'Bengaluru': 'South', 'Hyderabad': 'South', 'Chennai': 'South',
    'Kolkata': 'East'
}
for city in sorted(df['City'].unique().tolist()):
    region = city_regions.get(city, 'Central')
    cursor.execute("INSERT INTO dim_cities (city_name, region) VALUES (?, ?)", (city, region))
conn.commit()
city_map = {row[1]: row[0] for row in cursor.execute("SELECT city_id, city_name FROM dim_cities").fetchall()}

# Loyalty Tiers & Fees
tier_fees = {
    'Non-Member': 0.0,
    'Silver': 299.0,
    'Gold': 599.0,
    'Platinum': 999.0
}
for tier, fee in tier_fees.items():
    cursor.execute("INSERT INTO dim_loyalty_tiers (tier_name, annual_fee_inr) VALUES (?, ?)", (tier, fee))
conn.commit()
tier_map = {row[1]: row[0] for row in cursor.execute("SELECT tier_id, tier_name FROM dim_loyalty_tiers").fetchall()}

# Customers & Orders
print("[INFO] Populating Customers and Sales Transactions...")
# In this transactional dataset, each row represents an order with customer profile attributes.
# We create a customer entity per unique profile or order sequence
cust_rows = []
sales_rows = []

for idx, r in df.iterrows():
    cust_code = f"CUST-{idx+1:05d}"
    cursor.execute(
        """INSERT INTO dim_customers 
           (customer_code, city_id, tier_id, tenure_years, monthly_store_visits, app_logins_month, orders_per_year) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (cust_code, city_map[r['City']], tier_map[r['Loyalty_Tier']], int(r['Customer_Tenure_Years']),
         int(r['Monthly_Store_Visits']), int(r['App_Logins_Month']), int(r['Orders_Per_Year']))
    )
    cust_id = cursor.lastrowid
    
    sales_rows.append((
        r['Order_ID'],
        r['Formatted_Date'],
        cust_id,
        prod_map[r['Product']],
        ch_map[r['Channel']],
        int(r['Avg_Basket_Items']),
        int(r['Returns']),
        float(r['Customer_Rating']),
        float(r['Order_Value_INR']),
        float(r['Membership_Revenue_INR']),
        float(r['Annual_Spend_Est_INR'])
    ))

cursor.executemany(
    """INSERT INTO fact_sales 
       (order_id, order_date, customer_id, product_id, channel_id, basket_items, returns_flag, customer_rating, order_value_inr, membership_revenue_inr, annual_spend_est_inr)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    sales_rows
)
conn.commit()

# Create Analytical View
cursor.execute("""
CREATE VIEW IF NOT EXISTS v_retail_sales_analytical AS
SELECT 
    fs.order_id,
    fs.order_date,
    STRFTIME('%Y', fs.order_date) AS order_year,
    STRFTIME('%m', fs.order_date) AS order_month,
    cat.category_name AS category,
    prod.product_name AS product,
    ch.channel_name AS channel,
    cit.city_name AS city,
    cit.region,
    lt.tier_name AS loyalty_tier,
    cust.tenure_years AS customer_tenure_years,
    cust.monthly_store_visits,
    cust.app_logins_month,
    cust.orders_per_year,
    fs.basket_items AS avg_basket_items,
    fs.returns_flag AS returns,
    fs.customer_rating,
    fs.order_value_inr,
    fs.membership_revenue_inr,
    fs.annual_spend_est_inr,
    (fs.order_value_inr + fs.membership_revenue_inr) AS total_revenue_inr
FROM fact_sales fs
JOIN dim_customers cust ON fs.customer_id = cust.customer_id
JOIN dim_products prod ON fs.product_id = prod.product_id
JOIN dim_categories cat ON prod.category_id = cat.category_id
JOIN dim_channels ch ON fs.channel_id = ch.channel_id
JOIN dim_cities cit ON cust.city_id = cit.city_id
JOIN dim_loyalty_tiers lt ON cust.tier_id = lt.tier_id;
""")
conn.commit()

# Execute Verification Queries
print("\n[INFO] Running verification queries...")
res = cursor.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
print(f"-> Fact Sales Count: {res} rows")

cat_summary = pd.read_sql_query("""
    SELECT cat.category_name, COUNT(fs.order_id) AS orders, ROUND(SUM(fs.order_value_inr), 2) AS total_sales_inr
    FROM fact_sales fs
    JOIN dim_products prod ON fs.product_id = prod.product_id
    JOIN dim_categories cat ON prod.category_id = cat.category_id
    GROUP BY cat.category_name
    ORDER BY total_sales_inr DESC;
""", conn)
print("\n=== Category Performance from Database ===")
print(cat_summary.to_string(index=False))

# Export sample seed SQL statements
print(f"\n[INFO] Exporting sample seed script to {SEED_SQL_PATH}...")
with open(SEED_SQL_PATH, "w", encoding="utf-8") as f:
    f.write("-- Sample Seed Data for MySQL / SQLite Portability\n")
    f.write("-- Dimension records\n")
    for cat in categories:
        f.write(f"INSERT INTO dim_categories (category_name) VALUES ('{cat}');\n")
    for ch in channels:
        f.write(f"INSERT INTO dim_channels (channel_name) VALUES ('{ch}');\n")
    for city, reg in city_regions.items():
        f.write(f"INSERT INTO dim_cities (city_name, region) VALUES ('{city}', '{reg}');\n")
    for tier, fee in tier_fees.items():
        f.write(f"INSERT INTO dim_loyalty_tiers (tier_name, annual_fee_inr) VALUES ('{tier}', {fee});\n")
    f.write("\n-- First 50 Fact Records for Seed Reference\n")
    for s in sales_rows[:50]:
        f.write(f"INSERT INTO fact_sales (order_id, order_date, customer_id, product_id, channel_id, basket_items, returns_flag, customer_rating, order_value_inr, membership_revenue_inr, annual_spend_est_inr) VALUES ('{s[0]}', '{s[1]}', {s[2]}, {s[3]}, {s[4]}, {s[5]}, {s[6]}, {s[7]}, {s[8]}, {s[9]}, {s[10]});\n")

conn.close()
print("[SUCCESS] Stage 1: SQL Data Management complete and validated.")
