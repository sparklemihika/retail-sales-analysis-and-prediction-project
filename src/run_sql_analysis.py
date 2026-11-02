import os
import sqlite3
import pandas as pd

BASE_DIR = r"C:\Users\LENOVO\.gemini\antigravity\scratch\retail_sales_project"
DB_PATH = os.path.join(BASE_DIR, "data", "retail_sales.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

queries = {
    "1_top_products_by_category": """
        SELECT 
            cat.category_name,
            prod.product_name,
            COUNT(fs.order_id) AS total_orders,
            ROUND(SUM(fs.order_value_inr), 2) AS total_sales_inr,
            ROUND(AVG(fs.order_value_inr), 2) AS avg_order_value_inr,
            ROUND(AVG(fs.customer_rating), 2) AS avg_rating,
            DENSE_RANK() OVER (PARTITION BY cat.category_name ORDER BY SUM(fs.order_value_inr) DESC) AS category_rank
        FROM fact_sales fs
        JOIN dim_products prod ON fs.product_id = prod.product_id
        JOIN dim_categories cat ON prod.category_id = cat.category_id
        GROUP BY cat.category_name, prod.product_name
        ORDER BY cat.category_name, total_sales_inr DESC;
    """,
    "2_monthly_sales_mom_growth": """
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
            ROUND(((total_revenue_inr - LAG(total_revenue_inr, 1) OVER (ORDER BY sales_month)) 
            / LAG(total_revenue_inr, 1) OVER (ORDER BY sales_month)) * 100, 2) AS mom_growth_pct
        FROM MonthlyMetrics
        ORDER BY sales_month;
    """,
    "3_yoy_sales_growth": """
        SELECT 
            STRFTIME('%Y', fs.order_date) AS order_year,
            COUNT(fs.order_id) AS total_orders,
            ROUND(SUM(fs.order_value_inr), 2) AS sales_revenue_inr,
            ROUND(SUM(fs.membership_revenue_inr), 2) AS membership_revenue_inr,
            ROUND(SUM(fs.order_value_inr + fs.membership_revenue_inr), 2) AS gross_revenue_inr,
            ROUND(AVG(fs.order_value_inr), 2) AS aov_inr,
            ROUND((SUM(fs.order_value_inr) - LAG(SUM(fs.order_value_inr), 1) OVER (ORDER BY STRFTIME('%Y', fs.order_date)))
            / LAG(SUM(fs.order_value_inr), 1) OVER (ORDER BY STRFTIME('%Y', fs.order_date)) * 100, 2) AS yoy_sales_growth_pct
        FROM fact_sales fs
        GROUP BY STRFTIME('%Y', fs.order_date)
        ORDER BY order_year;
    """,
    "4_channel_performance": """
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
    """,
    "5_city_performance": """
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
    """,
    "6_loyalty_tier_analysis": """
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
    """,
    "7_category_returns_ratings": """
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
    """
}

output_md_path = os.path.join(REPORTS_DIR, "sql_analysis_results.md")
with open(output_md_path, "w", encoding="utf-8") as f_out:
    f_out.write("# SQL Analytical Query Results & Business Insights\n\n")
    f_out.write("Executed on SQLite/MySQL Relational Database for Project 1.\n\n")
    
    for q_name, q_sql in queries.items():
        print(f"[INFO] Executing {q_name}...")
        df_res = pd.read_sql_query(q_sql, conn)
        # Export CSV
        df_res.to_csv(os.path.join(REPORTS_DIR, f"{q_name}.csv"), index=False)
        # Append to Markdown
        f_out.write(f"## {q_name.replace('_', ' ').title()}\n\n")
        f_out.write(df_res.to_markdown(index=False) + "\n\n")

conn.close()
print(f"[SUCCESS] All analytical queries executed and exported to {REPORTS_DIR}")
