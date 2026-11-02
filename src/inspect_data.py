import pandas as pd
import numpy as np

csv_path = r"C:\Users\LENOVO\.gemini\antigravity\scratch\retail_sales_project\data\retail_sales_clean.csv"
df = pd.read_csv(csv_path)

print("=== DATASET OVERVIEW ===")
print("Shape:", df.shape)
print("\n=== COLUMNS & TYPES ===")
print(df.dtypes)

print("\n=== MISSING VALUES ===")
print(df.isnull().sum())

print("\n=== DUPLICATES ===")
print("Duplicate rows:", df.duplicated().sum())

print("\n=== HEAD (3 ROWS) ===")
print(df.head(3).T)

print("\n=== VALUE COUNTS ===")
print("Categories:", df['Category'].value_counts())
print("\nProducts:", df['Product'].value_counts())
print("\nChannels:", df['Channel'].value_counts())
print("\nLoyalty Tiers:", df['Loyalty_Tier'].value_counts())
print("\nCities (Top 10):", df['City'].value_counts())

print("\n=== ORDER VALUE STATS ===")
print(df['Order_Value_INR'].describe())

print("\n=== ANNUAL SPEND STATS ===")
print(df['Annual_Spend_Est_INR'].describe())

print("\n=== DATE RANGE ===")
df['Parsed_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
print("Min Date:", df['Parsed_Date'].min())
print("Max Date:", df['Parsed_Date'].max())
print("Years:", df['Parsed_Date'].dt.year.value_counts().sort_index())
