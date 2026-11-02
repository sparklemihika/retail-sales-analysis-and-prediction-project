-- ==============================================================================
-- PROJECT 1: RETAIL SALES PREDICTION AND ANALYSIS
-- Relational Database Schema (MySQL & SQLite Compatible DDL)
-- Stage 1: SQL - Data Management
-- ==============================================================================

-- Drop tables in reverse order of foreign key dependency if they exist
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_categories;
DROP TABLE IF EXISTS dim_channels;
DROP TABLE IF EXISTS dim_cities;
DROP TABLE IF EXISTS dim_loyalty_tiers;

-- ------------------------------------------------------------------------------
-- 1. Dimension Table: Categories
-- ------------------------------------------------------------------------------
CREATE TABLE dim_categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. Dimension Table: Products
-- ------------------------------------------------------------------------------
CREATE TABLE dim_products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(150) NOT NULL UNIQUE,
    category_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES dim_categories (category_id)
);

-- ------------------------------------------------------------------------------
-- 3. Dimension Table: Channels
-- ------------------------------------------------------------------------------
CREATE TABLE dim_channels (
    channel_id INT PRIMARY KEY AUTO_INCREMENT,
    channel_name VARCHAR(50) NOT NULL UNIQUE
);

-- ------------------------------------------------------------------------------
-- 4. Dimension Table: Cities (Geographic Dimension)
-- ------------------------------------------------------------------------------
CREATE TABLE dim_cities (
    city_id INT PRIMARY KEY AUTO_INCREMENT,
    city_name VARCHAR(100) NOT NULL UNIQUE,
    region VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 5. Dimension Table: Loyalty Tiers
-- ------------------------------------------------------------------------------
CREATE TABLE dim_loyalty_tiers (
    tier_id INT PRIMARY KEY AUTO_INCREMENT,
    tier_name VARCHAR(50) NOT NULL UNIQUE,
    annual_fee_inr DECIMAL(10, 2) NOT NULL DEFAULT 0.00
);

-- ------------------------------------------------------------------------------
-- 6. Dimension Table: Customers
-- ------------------------------------------------------------------------------
CREATE TABLE dim_customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_code VARCHAR(50) UNIQUE,
    city_id INT NOT NULL,
    tier_id INT NOT NULL,
    tenure_years INT NOT NULL DEFAULT 0,
    monthly_store_visits INT NOT NULL DEFAULT 0,
    app_logins_month INT NOT NULL DEFAULT 0,
    orders_per_year INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cust_city FOREIGN KEY (city_id) REFERENCES dim_cities (city_id),
    CONSTRAINT fk_cust_tier FOREIGN KEY (tier_id) REFERENCES dim_loyalty_tiers (tier_id)
);

-- ------------------------------------------------------------------------------
-- 7. Fact Table: Sales Transactions
-- ------------------------------------------------------------------------------
CREATE TABLE fact_sales (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    order_date DATE NOT NULL,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    channel_id INT NOT NULL,
    basket_items INT NOT NULL DEFAULT 1,
    returns_flag TINYINT(1) NOT NULL DEFAULT 0,
    customer_rating DECIMAL(3, 2) NOT NULL,
    order_value_inr DECIMAL(12, 2) NOT NULL,
    membership_revenue_inr DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    annual_spend_est_inr DECIMAL(14, 2) NOT NULL,
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id),
    CONSTRAINT fk_sales_product FOREIGN KEY (product_id) REFERENCES dim_products (product_id),
    CONSTRAINT fk_sales_channel FOREIGN KEY (channel_id) REFERENCES dim_channels (channel_id)
);

-- Indexes for Query Performance & Analytics
CREATE INDEX idx_sales_order_date ON fact_sales(order_date);
CREATE INDEX idx_sales_product ON fact_sales(product_id);
CREATE INDEX idx_sales_customer ON fact_sales(customer_id);
CREATE INDEX idx_sales_channel ON fact_sales(channel_id);

-- ------------------------------------------------------------------------------
-- 8. Unified Analytical View (De-normalized for Power BI & SQL Reporting)
-- ------------------------------------------------------------------------------
CREATE VIEW v_retail_sales_analytical AS
SELECT 
    fs.order_id,
    fs.order_date,
    YEAR(fs.order_date) AS order_year,
    MONTH(fs.order_date) AS order_month,
    QUARTER(fs.order_date) AS order_quarter,
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
