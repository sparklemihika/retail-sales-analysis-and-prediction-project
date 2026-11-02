-- ==============================================================================
-- PROJECT 1: RETAIL SALES PREDICTION AND ANALYSIS
-- Stage 1: SQL Analytical Queries (JOIN, GROUP BY, Aggregations & Window Functions)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1: Top Performing Products within each Category (Window Function)
-- Objective: Rank products by total sales revenue within their category
-- ------------------------------------------------------------------------------
SELECT 
    cat.category_name,
    prod.product_name,
    COUNT(fs.order_id) AS total_orders,
    ROUND(SUM(fs.order_value_inr), 2) AS total_sales_inr,
    ROUND(AVG(fs.order_value_inr), 2) AS avg_order_value_inr,
    ROUND(AVG(fs.customer_rating), 2) AS avg_rating,
    DENSE_RANK() OVER (
        PARTITION BY cat.category_name 
        ORDER BY SUM(fs.order_value_inr) DESC
    ) AS category_rank
FROM fact_sales fs
JOIN dim_products prod ON fs.product_id = prod.product_id
JOIN dim_categories cat ON prod.category_id = cat.category_id
GROUP BY cat.category_name, prod.product_name
ORDER BY cat.category_name, total_sales_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 2: Monthly Sales Performance & Month-over-Month (MoM) Growth
-- Objective: Evaluate seasonal dynamics and MoM revenue trajectory
-- ------------------------------------------------------------------------------
WITH MonthlyMetrics AS (
    SELECT 
        STRFTIME('%Y-%m', fs.order_date) AS sales_month,
        COUNT(fs.order_id) AS order_volume,
        ROUND(SUM(fs.order_value_inr), 2) AS total_revenue_inr,
        ROUND(AVG(fs.order_value_inr), 2) AS avg_order_value
    FROM fact_sales fs
    GROUP BY STRFTIME('%Y-%m', fs.order_date)
)
SELECT 
    sales_month,
    order_volume,
    total_revenue_inr,
    avg_order_value,
    LAG(total_revenue_inr, 1) OVER (ORDER BY sales_month) AS prev_month_revenue,
    ROUND(
        ((total_revenue_inr - LAG(total_revenue_inr, 1) OVER (ORDER BY sales_month)) 
        / LAG(total_revenue_inr, 1) OVER (ORDER BY sales_month)) * 100, 2
    ) AS mom_growth_pct
FROM MonthlyMetrics
ORDER BY sales_month;


-- ------------------------------------------------------------------------------
-- Query 3: Year-over-Year (YoY) Sales Comparison (2022 - 2025)
-- Objective: Assess annual revenue growth and order expansion
-- ------------------------------------------------------------------------------
SELECT 
    STRFTIME('%Y', fs.order_date) AS order_year,
    COUNT(fs.order_id) AS total_orders,
    ROUND(SUM(fs.order_value_inr), 2) AS sales_revenue_inr,
    ROUND(SUM(fs.membership_revenue_inr), 2) AS membership_revenue_inr,
    ROUND(SUM(fs.order_value_inr + fs.membership_revenue_inr), 2) AS gross_revenue_inr,
    ROUND(AVG(fs.order_value_inr), 2) AS aov_inr,
    ROUND(
        (SUM(fs.order_value_inr) - LAG(SUM(fs.order_value_inr), 1) OVER (ORDER BY STRFTIME('%Y', fs.order_date)))
        / LAG(SUM(fs.order_value_inr), 1) OVER (ORDER BY STRFTIME('%Y', fs.order_date)) * 100, 2
    ) AS yoy_sales_growth_pct
FROM fact_sales fs
GROUP BY STRFTIME('%Y', fs.order_date)
ORDER BY order_year;


-- ------------------------------------------------------------------------------
-- Query 4: Channel Share, Basket Size, and Revenue Contribution
-- Objective: Compare In-Store, Mobile App, and Online performance
-- ------------------------------------------------------------------------------
SELECT 
    ch.channel_name,
    COUNT(fs.order_id) AS total_transactions,
    ROUND(COUNT(fs.order_id) * 100.0 / (SELECT COUNT(*) FROM fact_sales), 2) AS transaction_share_pct,
    ROUND(SUM(fs.order_value_inr), 2) AS total_sales_inr,
    ROUND(SUM(fs.order_value_inr) * 100.0 / (SELECT SUM(order_value_inr) FROM fact_sales), 2) AS revenue_share_pct,
    ROUND(AVG(fs.basket_items), 2) AS avg_items_per_basket,
    ROUND(AVG(fs.order_value_inr), 2) AS avg_order_value_inr,
    ROUND(AVG(fs.returns_flag) * 100, 2) AS return_rate_pct
FROM fact_sales fs
JOIN dim_channels ch ON fs.channel_id = ch.channel_id
GROUP BY ch.channel_name
ORDER BY total_sales_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 5: City-Level Sales & Regional Penetration
-- Objective: Identify high-yield geographical retail hubs
-- ------------------------------------------------------------------------------
SELECT 
    cit.city_name,
    cit.region,
    COUNT(DISTINCT cust.customer_id) AS active_customers,
    COUNT(fs.order_id) AS total_orders,
    ROUND(SUM(fs.order_value_inr), 2) AS city_sales_inr,
    ROUND(AVG(fs.order_value_inr), 2) AS avg_order_value_inr,
    ROUND(SUM(fs.annual_spend_est_inr), 2) AS total_est_annual_spend_inr
FROM fact_sales fs
JOIN dim_customers cust ON fs.customer_id = cust.customer_id
JOIN dim_cities cit ON cust.city_id = cit.city_id
GROUP BY cit.city_name, cit.region
ORDER BY city_sales_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 6: Loyalty Tier Value Creation & Membership Revenue Impact
-- Objective: Measure customer retention, ticket size, and tier ROI
-- ------------------------------------------------------------------------------
SELECT 
    lt.tier_name,
    lt.annual_fee_inr,
    COUNT(DISTINCT cust.customer_id) AS total_members,
    ROUND(SUM(fs.order_value_inr), 2) AS gross_order_value_inr,
    ROUND(SUM(fs.membership_revenue_inr), 2) AS total_membership_fee_inr,
    ROUND(AVG(fs.order_value_inr), 2) AS aov_per_tier,
    ROUND(AVG(cust.orders_per_year), 1) AS avg_orders_per_year,
    ROUND(AVG(fs.annual_spend_est_inr), 2) AS avg_est_annual_spend_inr
FROM fact_sales fs
JOIN dim_customers cust ON fs.customer_id = cust.customer_id
JOIN dim_loyalty_tiers lt ON cust.tier_id = lt.tier_id
GROUP BY lt.tier_name, lt.annual_fee_inr
ORDER BY gross_order_value_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 7: Return Rate & Customer Satisfaction by Category
-- Objective: Pinpoint high-return product categories and correlation with ratings
-- ------------------------------------------------------------------------------
SELECT 
    cat.category_name,
    COUNT(fs.order_id) AS total_orders,
    SUM(fs.returns_flag) AS total_returns,
    ROUND(SUM(fs.returns_flag) * 100.0 / COUNT(fs.order_id), 2) AS return_rate_pct,
    ROUND(AVG(fs.customer_rating), 2) AS avg_rating,
    ROUND(AVG(fs.order_value_inr), 2) AS avg_ticket_size_inr
FROM fact_sales fs
JOIN dim_products prod ON fs.product_id = prod.product_id
JOIN dim_categories cat ON prod.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY return_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- Query 8: Omnichannel Engagement Analysis (App Logins vs Store Visits)
-- Objective: Segment customers by physical vs. digital engagement
-- ------------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN cust.app_logins_month >= 15 AND cust.monthly_store_visits >= 5 THEN 'Omnichannel Power User'
        WHEN cust.app_logins_month >= 15 THEN 'Digital Heavy'
        WHEN cust.monthly_store_visits >= 5 THEN 'In-Store Shopper'
        ELSE 'Casual Shopper'
    END AS engagement_segment,
    COUNT(DISTINCT cust.customer_id) AS customer_count,
    ROUND(AVG(fs.order_value_inr), 2) AS avg_order_value,
    ROUND(AVG(fs.basket_items), 2) AS avg_basket_items,
    ROUND(AVG(fs.annual_spend_est_inr), 2) AS avg_annual_spend
FROM fact_sales fs
JOIN dim_customers cust ON fs.customer_id = cust.customer_id
GROUP BY 1
ORDER BY avg_annual_spend DESC;


-- ------------------------------------------------------------------------------
-- Query 9: Top 10 High-Value Customers (RFM Proxy)
-- Objective: Identify key enterprise/VIP retail consumers
-- ------------------------------------------------------------------------------
SELECT 
    cust.customer_code,
    cit.city_name,
    lt.tier_name AS loyalty_tier,
    cust.tenure_years,
    cust.orders_per_year,
    COUNT(fs.order_id) AS logged_orders,
    ROUND(SUM(fs.order_value_inr), 2) AS total_actual_spend_inr,
    ROUND(AVG(fs.annual_spend_est_inr), 2) AS estimated_annual_spend_inr
FROM fact_sales fs
JOIN dim_customers cust ON fs.customer_id = cust.customer_id
JOIN dim_cities cit ON cust.city_id = cit.city_id
JOIN dim_loyalty_tiers lt ON cust.tier_id = lt.tier_id
GROUP BY cust.customer_code, cit.city_name, lt.tier_name, cust.tenure_years, cust.orders_per_year
ORDER BY estimated_annual_spend_inr DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- Query 10: ML Feature Extraction Dataset View
-- Objective: Extract structured tabular dataset for ML pipeline training
-- ------------------------------------------------------------------------------
SELECT 
    fs.order_id,
    fs.order_date,
    STRFTIME('%Y', fs.order_date) AS order_year,
    STRFTIME('%m', fs.order_date) AS order_month,
    STRFTIME('%w', fs.order_date) AS day_of_week,
    cat.category_name AS category,
    prod.product_name AS product,
    ch.channel_name AS channel,
    cit.city_name AS city,
    lt.tier_name AS loyalty_tier,
    cust.tenure_years,
    cust.monthly_store_visits,
    cust.app_logins_month,
    cust.orders_per_year,
    fs.basket_items,
    fs.returns_flag,
    fs.customer_rating,
    fs.membership_revenue_inr,
    fs.order_value_inr AS target_order_value_inr
FROM fact_sales fs
JOIN dim_customers cust ON fs.customer_id = cust.customer_id
JOIN dim_products prod ON fs.product_id = prod.product_id
JOIN dim_categories cat ON prod.category_id = cat.category_id
JOIN dim_channels ch ON fs.channel_id = ch.channel_id
JOIN dim_cities cit ON cust.city_id = cit.city_id
JOIN dim_loyalty_tiers lt ON cust.tier_id = lt.tier_id;
