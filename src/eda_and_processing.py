import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

BASE_DIR = r"C:\Users\LENOVO\.gemini\antigravity\scratch\retail_sales_project"
CSV_PATH = os.path.join(BASE_DIR, "data", "retail_sales_clean.csv")
FIG_DIR = os.path.join(BASE_DIR, "reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

print("[INFO] Loading dataset for EDA...")
df = pd.read_csv(CSV_PATH)
df['Parsed_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
df['Year'] = df['Parsed_Date'].dt.year
df['Month'] = df['Parsed_Date'].dt.month
df['Year_Month'] = df['Parsed_Date'].dt.to_period('M').astype(str)
df['DayOfWeek'] = df['Parsed_Date'].dt.day_name()
df['Quarter'] = 'Q' + df['Parsed_Date'].dt.quarter.astype(str)

print(f"[INFO] Dataset shape: {df.shape}")

# ------------------------------------------------------------------------------
# 1. Category Revenue, Order Volume & AOV
# ------------------------------------------------------------------------------
print("[INFO] Generating 01_category_revenue_and_orders.png...")
cat_grp = df.groupby('Category').agg(
    total_sales=('Order_Value_INR', 'sum'),
    order_count=('Order_ID', 'count'),
    aov=('Order_Value_INR', 'mean')
).sort_values('total_sales', ascending=False).reset_index()

fig, ax1 = plt.subplots(figsize=(11, 6))
bars = ax1.bar(cat_grp['Category'], cat_grp['total_sales'] / 1e6, color='#2563EB', width=0.55, label='Total Revenue (₹ Millions)')
ax1.set_ylabel('Total Revenue (₹ Millions)', color='#2563EB', fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#2563EB')
ax1.set_xticklabels(cat_grp['Category'], rotation=20, ha='right', fontsize=11)

ax2 = ax1.twinx()
line = ax2.plot(cat_grp['Category'], cat_grp['aov'], color='#DC2626', marker='o', linewidth=2.5, markersize=8, label='Avg Order Value (AOV ₹)')
ax2.set_ylabel('Average Order Value (₹)', color='#DC2626', fontsize=12, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='#DC2626')
ax2.grid(False)

# Annotate bars
for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"₹{yval:.1f}M", ha='center', va='bottom', fontsize=9, fontweight='semibold')

plt.title('Retail Sales Revenue & Average Order Value (AOV) by Category', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '01_category_revenue_and_orders.png'), dpi=300)
plt.close()

# ------------------------------------------------------------------------------
# 2. Monthly Sales Trend & Seasonality (2022 - 2025)
# ------------------------------------------------------------------------------
print("[INFO] Generating 02_monthly_sales_trend_and_seasonality.png...")
monthly_sales = df.groupby('Year_Month')['Order_Value_INR'].sum().reset_index()
monthly_sales['Sales_Millions'] = monthly_sales['Order_Value_INR'] / 1e6

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(monthly_sales['Year_Month'], monthly_sales['Sales_Millions'], marker='o', color='#0284C7', linewidth=2.2, markersize=5)
ax.fill_between(monthly_sales['Year_Month'], monthly_sales['Sales_Millions'], color='#BAE6FD', alpha=0.4)

# Highlight October festive spikes
for idx, row in monthly_sales.iterrows():
    if row['Year_Month'].endswith('-10'):
        ax.annotate(f"Diwali Spike\n₹{row['Sales_Millions']:.2f}M", 
                    (idx, row['Sales_Millions']),
                    textcoords="offset points", xytext=(0, 18), ha='center',
                    fontweight='bold', color='#B91C1C', fontsize=9,
                    arrowprops=dict(arrowstyle="->", color='#B91C1C', lw=1.2))

ax.set_xticks(range(0, len(monthly_sales), 3))
ax.set_xticklabels(monthly_sales['Year_Month'].iloc[::3], rotation=45, ha='right')
ax.set_title('4-Year Monthly Revenue Trajectory & Festive Seasonality (2022 - 2025)', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('Monthly Revenue (₹ Millions)', fontsize=12, fontweight='bold')
ax.set_xlabel('Year-Month', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '02_monthly_sales_trend_and_seasonality.png'), dpi=300)
plt.close()

# ------------------------------------------------------------------------------
# 3. Omnichannel Performance (In-Store vs Online vs Mobile App)
# ------------------------------------------------------------------------------
print("[INFO] Generating 03_channel_performance_and_basket.png...")
ch_agg = df.groupby('Channel').agg(
    Revenue=('Order_Value_INR', 'sum'),
    Transactions=('Order_ID', 'count'),
    Avg_Basket=('Avg_Basket_Items', 'mean'),
    Returns_Pct=('Returns', lambda x: (x > 0).mean() * 100)
).reset_index()

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
colors = ['#3B82F6', '#10B981', '#F59E0B']

# Revenue Share Pie
axes[0].pie(ch_agg['Revenue'], labels=ch_agg['Channel'], autopct='%1.1f%%', colors=colors, startangle=140, explode=[0.05, 0, 0])
axes[0].set_title('Revenue Share by Channel', fontsize=12, fontweight='bold')

# Avg Basket Items Bar
axes[1].bar(ch_agg['Channel'], ch_agg['Avg_Basket'], color=colors, width=0.5)
axes[1].set_ylabel('Average Basket Items', fontsize=11, fontweight='bold')
axes[1].set_title('Avg Basket Size by Channel', fontsize=12, fontweight='bold')
for i, v in enumerate(ch_agg['Avg_Basket']):
    axes[1].text(i, v + 0.05, f"{v:.2f}", ha='center', fontweight='bold')

# Return Rate Bar
axes[2].bar(ch_agg['Channel'], ch_agg['Returns_Pct'], color=['#EF4444', '#F87171', '#FCA5A5'], width=0.5)
axes[2].set_ylabel('Orders with Returns (%)', fontsize=11, fontweight='bold')
axes[2].set_title('Return Rate (%) by Channel', fontsize=12, fontweight='bold')
for i, v in enumerate(ch_agg['Returns_Pct']):
    axes[2].text(i, v + 0.4, f"{v:.1f}%", ha='center', fontweight='bold')

plt.suptitle('Omnichannel Retail Metrics Comparison', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '03_channel_performance_and_basket.png'), dpi=300)
plt.close()

# ------------------------------------------------------------------------------
# 4. City Sales Distribution (Top Indian Metro Markets)
# ------------------------------------------------------------------------------
print("[INFO] Generating 04_city_sales_distribution.png...")
city_grp = df.groupby('City')['Order_Value_INR'].sum().sort_values(ascending=True) / 1e6

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(city_grp.index, city_grp.values, color='#0D9488', height=0.65)
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.1, bar.get_y() + bar.get_height()/2.0, f"₹{w:.2f}M", va='center', ha='left', fontsize=10, fontweight='semibold')

ax.set_title('Total Sales Revenue across 10 Metropolitan Cities (₹ Millions)', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Revenue (₹ Millions)', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '04_city_sales_distribution.png'), dpi=300)
plt.close()

# ------------------------------------------------------------------------------
# 5. Loyalty Tier Analysis & Membership Economics
# ------------------------------------------------------------------------------
print("[INFO] Generating 05_loyalty_tier_comparison.png...")
tier_order = ['Non-Member', 'Silver', 'Gold', 'Platinum']
tier_df = df.groupby('Loyalty_Tier').agg(
    Member_Count=('Order_ID', 'count'),
    Avg_Annual_Spend=('Annual_Spend_Est_INR', 'mean'),
    Membership_Rev=('Membership_Revenue_INR', 'sum'),
    AOV=('Order_Value_INR', 'mean')
).reindex(tier_order).reset_index()

fig, ax1 = plt.subplots(figsize=(11, 5.5))
bars = ax1.bar(tier_df['Loyalty_Tier'], tier_df['Avg_Annual_Spend'] / 1e3, color='#8B5CF6', width=0.5, label='Avg Annual Spend (₹ Thousands)')
ax1.set_ylabel('Avg Annual Spend (₹ Thousands)', color='#8B5CF6', fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#8B5CF6')

ax2 = ax1.twinx()
line = ax2.plot(tier_df['Loyalty_Tier'], tier_df['Membership_Rev'] / 1e3, color='#F59E0B', marker='s', linewidth=2.5, markersize=8, label='Membership Fees (₹ Thousands)')
ax2.set_ylabel('Total Membership Fee Revenue (₹ Thousands)', color='#F59E0B', fontsize=12, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='#F59E0B')
ax2.grid(False)

for bar in bars:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, h + 1, f"₹{h:.1f}k", ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.title('Loyalty Program Financial Impact: Spend Multiplier vs Fee Revenue', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '05_loyalty_tier_comparison.png'), dpi=300)
plt.close()

# ------------------------------------------------------------------------------
# 6. Customer Engagement Matrix: Logins vs Store Visits vs Order Value
# ------------------------------------------------------------------------------
print("[INFO] Generating 06_customer_engagement_matrix.png...")
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(
    df['Monthly_Store_Visits'], 
    df['App_Logins_Month'], 
    c=df['Order_Value_INR'], 
    cmap='viridis', 
    alpha=0.6, 
    s=df['Avg_Basket_Items'] * 15,
    edgecolors='none'
)
cbar = plt.colorbar(scatter)
cbar.set_label('Order Value (INR)', fontsize=11, fontweight='bold')
ax.set_xlabel('Monthly Store Visits', fontsize=12, fontweight='bold')
ax.set_ylabel('Monthly App Logins', fontsize=12, fontweight='bold')
ax.set_title('Omnichannel Customer Engagement vs. Order Value (Bubble size = Basket Items)', fontsize=13, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '06_customer_engagement_matrix.png'), dpi=300)
plt.close()

# ------------------------------------------------------------------------------
# 7. Correlation Heatmap
# ------------------------------------------------------------------------------
print("[INFO] Generating 07_correlation_heatmap.png...")
num_cols = [
    'Customer_Tenure_Years', 'Monthly_Store_Visits', 'Avg_Basket_Items',
    'App_Logins_Month', 'Orders_Per_Year', 'Returns', 'Customer_Rating',
    'Order_Value_INR', 'Membership_Revenue_INR', 'Annual_Spend_Est_INR'
]
corr_matrix = df[num_cols].corr()

fig, ax = plt.subplots(figsize=(11, 8.5))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, cbar_kws={'label': 'Correlation Coefficient'}, ax=ax, linewidths=0.5)
ax.set_title('Pearson Correlation Heatmap of Numerical Features', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '07_correlation_heatmap.png'), dpi=300)
plt.close()

# ------------------------------------------------------------------------------
# 8. Target Variable Distribution & Log Analysis
# ------------------------------------------------------------------------------
print("[INFO] Generating 08_order_value_distribution.png...")
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Raw distribution
sns.histplot(df['Order_Value_INR'], kde=True, ax=axes[0], color='#2563EB', bins=40)
axes[0].set_title(f"Raw Order Value Distribution\nSkewness: {df['Order_Value_INR'].skew():.2f}", fontsize=12, fontweight='bold')
axes[0].set_xlabel('Order Value (INR)', fontsize=11)
axes[0].set_ylabel('Frequency', fontsize=11)

# Log-transformed distribution
log_sales = np.log1p(df['Order_Value_INR'])
sns.histplot(log_sales, kde=True, ax=axes[1], color='#059669', bins=40)
axes[1].set_title(f"Log1p Transformed Distribution\nSkewness: {log_sales.skew():.2f} (Near Normal)", fontsize=12, fontweight='bold')
axes[1].set_xlabel('log(1 + Order Value INR)', fontsize=11)
axes[1].set_ylabel('Frequency', fontsize=11)

plt.suptitle('Target Variable (Order Value) Distribution and Transformation Analysis', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '08_order_value_distribution.png'), dpi=300)
plt.close()

print("[SUCCESS] All 8 high-resolution EDA figures generated successfully in reports/figures/")
