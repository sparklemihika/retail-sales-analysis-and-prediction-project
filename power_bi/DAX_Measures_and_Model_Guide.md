# Power BI Data Model, DAX Measures & Dashboard Architecture Guide
## Project 1: Retail Sales Prediction and Analysis

This document provides the complete architecture, data schema, relationship definitions, DAX formulas, and visual wireframes required to deploy **Project 1** in **Microsoft Power BI Desktop / Service**.

---

## 1. Data Model Architecture (Star Schema)

The reporting data model follows an industry-standard **Star Schema** optimized for high-performance VertiPaq tabular engine evaluation.

```
                  +---------------------+
                  |   dim_categories    |
                  +---------------------+
                             |
                             | 1:N
                             v
+----------------+       +-------------------+       +--------------------+
|  dim_channels  | ----> |   dim_products    |       |     dim_cities     |
+----------------+ 1:N   +-------------------+       +--------------------+
                             |                                 |
                             | 1:N                             | 1:N
                             v                                 v
                     +-------------------+       1:N +--------------------+
                     |    fact_sales     | <-------- |   dim_customers    |
                     +-------------------+           +--------------------+
                             ^                                 ^
                             | 1:N                             | 1:N
                             |                                 |
                     +-------------------+           +--------------------+
                     |    dim_calendar   |           | dim_loyalty_tiers  |
                     +-------------------+           +--------------------+
```

### Table Relationships & Cardinalities

| From Table | From Column | To Table | To Column | Cardinality | Cross Filter | Active |
|:---|:---|:---|:---|:---|:---|:---|
| `fact_sales` | `product_id` | `dim_products` | `product_id` | Many-to-One (*:1) | Single | Yes |
| `dim_products` | `category_id` | `dim_categories` | `category_id` | Many-to-One (*:1) | Single | Yes |
| `fact_sales` | `channel_id` | `dim_channels` | `channel_id` | Many-to-One (*:1) | Single | Yes |
| `fact_sales` | `customer_id` | `dim_customers` | `customer_id` | Many-to-One (*:1) | Single | Yes |
| `dim_customers`| `city_id` | `dim_cities` | `city_id` | Many-to-One (*:1) | Single | Yes |
| `dim_customers`| `tier_id` | `dim_loyalty_tiers` | `tier_id` | Many-to-One (*:1) | Single | Yes |
| `fact_sales` | `order_date` | `dim_calendar` | `Date` | Many-to-One (*:1) | Single | Yes |

---

## 2. Dynamic Calendar Dimension (DAX Calculated Table)

Create a dedicated date table marked as the Official Date Table:

```dax
dim_calendar = 
VAR MinDate = DATE(2022, 1, 1)
VAR MaxDate = DATE(2025, 12, 31)
RETURN
    ADDCOLUMNS (
        CALENDAR(MinDate, MaxDate),
        "Year", YEAR([Date]),
        "Year Month", FORMAT([Date], "YYYY-MM"),
        "Month Name", FORMAT([Date], "MMMM"),
        "Month Number", MONTH([Date]),
        "Quarter", "Q" & FORMAT([Date], "Q"),
        "Year Quarter", FORMAT([Date], "YYYY") & "-Q" & FORMAT([Date], "Q"),
        "Day of Week", FORMAT([Date], "dddd"),
        "Day of Week Number", WEEKDAY([Date], 2), -- Monday = 1
        "Is Weekend", IF(WEEKDAY([Date], 2) >= 6, "Weekend", "Weekday"),
        "Is Festive Quarter", IF(MONTH([Date]) IN {10, 11, 12}, "Festive Season (Q4)", "Regular Period")
    )
```

---

## 3. Core Business & Analytical DAX Measures

Organize these inside a dedicated measure table: `_Measures`.

### 3.1 Financial & Volume KPIs

```dax
-- 1. Total Sales Revenue (INR)
Total Sales INR = 
SUM(fact_sales[order_value_inr])

-- 2. Total Membership Revenue (INR)
Total Membership Revenue INR = 
SUM(fact_sales[membership_revenue_inr])

-- 3. Gross Combined Revenue (INR)
Gross Revenue INR = 
[Total Sales INR] + [Total Membership Revenue INR]

-- 4. Total Orders (Volume)
Total Orders = 
COUNTROWS(fact_sales)

-- 5. Average Order Value (AOV)
AOV INR = 
DIVIDE([Total Sales INR], [Total Orders], 0)

-- 6. Total Basket Items Sold
Total Items Sold = 
SUM(fact_sales[basket_items])

-- 7. Average Basket Size (Items per Transaction)
Avg Basket Size = 
DIVIDE([Total Items Sold], [Total Orders], 0)
```

### 3.2 Time Intelligence (MoM, YoY, YTD)

```dax
-- 8. Sales Previous Year (SPLY)
Sales Last Year INR = 
CALCULATE(
    [Total Sales INR],
    SAMEPERIODLASTYEAR(dim_calendar[Date])
)

-- 9. Year-over-Year Sales Growth (Amount)
YoY Sales Growth INR = 
[Total Sales INR] - [Sales Last Year INR]

-- 10. Year-over-Year Sales Growth (%)
YoY Sales Growth % = 
DIVIDE([YoY Sales Growth INR], [Sales Last Year INR], BLANK())

-- 11. Sales Previous Month (MOM)
Sales Last Month INR = 
CALCULATE(
    [Total Sales INR],
    DATEADD(dim_calendar[Date], -1, MONTH)
)

-- 12. Month-over-Month Sales Growth (%)
MoM Sales Growth % = 
DIVIDE([Total Sales INR] - [Sales Last Month INR], [Sales Last Month INR], BLANK())

-- 13. Year-to-Date (YTD) Cumulative Sales
Sales YTD INR = 
TOTALYTD([Total Sales INR], dim_calendar[Date])
```

### 3.3 Customer Behavior & Channel Metrics

```dax
-- 14. Total Returned Transactions
Total Returns = 
CALCULATE(
    COUNTROWS(fact_sales),
    fact_sales[returns_flag] > 0
)

-- 15. Return Rate (%)
Return Rate % = 
DIVIDE([Total Returns], [Total Orders], 0)

-- 16. Average Customer Satisfaction Rating
Avg Customer Rating = 
AVERAGE(fact_sales[customer_rating])

-- 17. In-Store Channel Revenue Share (%)
InStore Share % = 
DIVIDE(
    CALCULATE([Total Sales INR], dim_channels[channel_name] = "In-Store"),
    [Total Sales INR],
    0
)

-- 18. Online & Mobile Digital Revenue Share (%)
Digital Share % = 
DIVIDE(
    CALCULATE([Total Sales INR], dim_channels[channel_name] IN {"Online", "Mobile App"}),
    [Total Sales INR],
    0
)
```

### 3.4 Machine Learning & Forecast Variance Measures

```dax
-- 19. Predicted Sales INR (from ML Model Export)
Predicted Sales INR = 
SUM(test_predictions[Predicted_Order_Value_INR])

-- 20. Actual Sales for Test Evaluation
Actual Sales Test INR = 
SUM(test_predictions[Actual_Order_Value_INR])

-- 21. Model Prediction Error / Variance
Forecast Variance INR = 
[Actual Sales Test INR] - [Predicted Sales INR]

-- 22. Mean Absolute Percentage Error (MAPE %)
Forecast MAPE % = 
AVERAGEX(
    test_predictions,
    DIVIDE(ABS(test_predictions[Actual_Order_Value_INR] - test_predictions[Predicted_Order_Value_INR]), test_predictions[Actual_Order_Value_INR], 0)
)

-- 23. Model Accuracy (%)
Forecast Accuracy % = 
1 - [Forecast MAPE %]
```

---

## 4. Power BI Multi-Page Dashboard Specification

### Page 1: Executive Sales Overview & Financial Health
- **Header Banner**: Current Filter Status, Last Refresh Date, Currency (INR).
- **KPI Cards (Top Bar)**:
  - Card 1: `Total Sales INR` (Formatted as ₹ Millions with YoY Growth % Callout).
  - Card 2: `Total Orders` (Count with MoM indicator).
  - Card 3: `AOV INR` (Average Order Value).
  - Card 4: `Gross Revenue INR` (Sales + Membership Fees).
  - Card 5: `Avg Customer Rating` (Star rating indicator).
- **Visual 1 (Area Chart - Center)**: Monthly Revenue Trend (2022–2025) with `dim_calendar[Year Month]` on X-axis, `[Total Sales INR]` on Y-axis, tooltips showing `[MoM Sales Growth %]`.
- **Visual 2 (Clustered Column Chart)**: Category Revenue & AOV Dual-Axis Chart.
- **Visual 3 (Donut Chart)**: Revenue Share by Channel (In-Store, Mobile App, Online).
- **Slicers (Top/Left)**: Year, Quarter, Channel, City.

### Page 2: Product & Category Deep Dive
- **Visual 1 (Decomposition Tree)**: Explain `Total Sales INR` decomposed by: `Category` -> `Product` -> `Channel` -> `City`.
- **Visual 2 (Matrix Table)**:
  - Rows: `Category`, `Product`.
  - Values: `Total Orders`, `Total Sales INR`, `AOV INR`, `Total Returns`, `Return Rate %`, `Avg Customer Rating`.
  - Conditional Formatting: Data bars on `Total Sales INR`, red gradient on `Return Rate %`.
- **Visual 3 (Scatter Plot)**: Avg Basket Size vs. AOV by Product (Bubble size = Total Orders).

### Page 3: Omnichannel & Customer Intelligence
- **Visual 1 (Map / Horizontal Bar)**: City Performance across the 10 Metro Hubs (Mumbai, Bengaluru, Delhi, etc.).
- **Visual 2 (100% Stacked Bar)**: Channel Distribution by City.
- **Visual 3 (Clustered Bar Chart)**: Loyalty Tier Economics (Spend Multiplier vs. Fee Revenue by Tier: Non-Member, Silver, Gold, Platinum).
- **Visual 4 (Quadrant Matrix)**: App Logins vs. Monthly Store Visits with dynamic segmentation.

### Page 4: Machine Learning Predictive Insights & Forecast Evaluation
- **Visual 1 (Scatter Plot with 45-degree Reference Line)**: Actual vs. Predicted Order Value (`test_predictions[Actual_Order_Value_INR]` vs `test_predictions[Predicted_Order_Value_INR]`).
- **Visual 2 (KPI Cards)**: Test $R^2$ Score (0.818), Test MAE (₹3,053.70), Test RMSE (₹5,273.10), Forecast Accuracy (83.4%).
- **Visual 3 (Horizontal Bar)**: Top 15 Feature Importances (Electronics, Headphones, Fashion, Avg Basket Items, Customer Engagement).
- **Visual 4 (Histogram / Column)**: Prediction Error Distribution (Residuals centered around 0).

---

## 5. Deployment & Data Source Configuration
1. Connect Power BI Desktop to `retail_sales_clean.csv` or SQLite ODBC / MySQL database (`retail_sales.db`).
2. Load dimension tables and `fact_sales`.
3. Create the `dim_calendar` table using the DAX code in Section 2.
4. Establish relationships as defined in Section 1.
5. Create a `_Measures` table and add all DAX measures from Section 3.
6. Publish to Power BI Service and schedule automated refreshes.
