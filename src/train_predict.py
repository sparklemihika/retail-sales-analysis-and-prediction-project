import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Paths
BASE_DIR = r"C:\Users\LENOVO\.gemini\antigravity\scratch\retail_sales_project"
CSV_PATH = os.path.join(BASE_DIR, "data", "retail_sales_clean.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
FIG_DIR = os.path.join(REPORTS_DIR, "figures")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

print("[INFO] Loading dataset for Feature Engineering & Model Training...")
df = pd.read_csv(CSV_PATH)
df['Parsed_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')

# ------------------------------------------------------------------------------
# 1. Feature Engineering
# ------------------------------------------------------------------------------
print("[INFO] Engineering temporal, behavioral, and engagement features...")
df['Order_Year'] = df['Parsed_Date'].dt.year
df['Order_Month'] = df['Parsed_Date'].dt.month
df['Order_Day'] = df['Parsed_Date'].dt.day
df['Day_Of_Week'] = df['Parsed_Date'].dt.dayofweek
df['Order_Quarter'] = df['Parsed_Date'].dt.quarter
df['Is_Weekend'] = df['Day_Of_Week'].isin([5, 6]).astype(int)
df['Is_Festive_Season'] = df['Order_Month'].isin([10, 11]).astype(int)

# Behavioral interaction ratios
df['Logins_Per_Visit'] = df['App_Logins_Month'] / (df['Monthly_Store_Visits'] + 1.0)
df['Omnichannel_Index'] = (df['App_Logins_Month'] * 0.5) + (df['Monthly_Store_Visits'] * 1.5)

# Target variable
y = df['Order_Value_INR']

# Feature matrix X (exclude target and direct derivative Annual_Spend_Est_INR to prevent data leakage)
feature_cols = [
    'Category', 'Product', 'Channel', 'City', 'Loyalty_Tier',
    'Customer_Tenure_Years', 'Monthly_Store_Visits', 'Avg_Basket_Items',
    'App_Logins_Month', 'Orders_Per_Year', 'Returns', 'Customer_Rating',
    'Membership_Revenue_INR', 'Order_Year', 'Order_Month', 'Order_Day',
    'Day_Of_Week', 'Order_Quarter', 'Is_Weekend', 'Is_Festive_Season',
    'Logins_Per_Visit', 'Omnichannel_Index'
]
X = df[feature_cols].copy()

# Categorical and numerical columns definition
categorical_cols = ['Category', 'Product', 'Channel', 'City', 'Loyalty_Tier']
numerical_cols = [c for c in feature_cols if c not in categorical_cols]

print(f"[INFO] Total feature count: {len(feature_cols)} (Categorical: {len(categorical_cols)}, Numerical: {len(numerical_cols)})")

# ------------------------------------------------------------------------------
# 2. Train-Test Split (80% Train, 20% Test)
# ------------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)
print(f"[INFO] Train samples: {X_train.shape[0]}, Test samples: {X_test.shape[0]}")

# ------------------------------------------------------------------------------
# 3. Preprocessor Pipeline
# ------------------------------------------------------------------------------
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
    ]
)

# ------------------------------------------------------------------------------
# 4. Model Training & Comparison
# ------------------------------------------------------------------------------
models = {
    'Dummy Regressor (Mean)': DummyRegressor(strategy='mean'),
    'Linear Regression': LinearRegression(),
    'Ridge Regression (alpha=1.0)': Ridge(alpha=1.0),
    'Decision Tree Regressor': DecisionTreeRegressor(max_depth=12, random_state=42),
    'Random Forest Regressor (Tuned)': RandomForestRegressor(
        n_estimators=200,
        max_depth=16,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
}

results = []
fitted_pipelines = {}

print("\n=== BENCHMARKING MODELS ===")
for name, model in models.items():
    pipe = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])
    
    # Train
    pipe.fit(X_train, y_train)
    fitted_pipelines[name] = pipe
    
    # Predict
    train_preds = pipe.predict(X_train)
    test_preds = pipe.predict(X_test)
    
    # Metrics
    train_mae = mean_absolute_error(y_train, train_preds)
    test_mae = mean_absolute_error(y_test, test_preds)
    
    train_mse = mean_squared_error(y_train, train_preds)
    test_mse = mean_squared_error(y_test, test_preds)
    
    train_rmse = np.sqrt(train_mse)
    test_rmse = np.sqrt(test_mse)
    
    train_r2 = r2_score(y_train, train_preds)
    test_r2 = r2_score(y_test, test_preds)
    
    results.append({
        'Model': name,
        'Train MAE (₹)': round(train_mae, 2),
        'Test MAE (₹)': round(test_mae, 2),
        'Train RMSE (₹)': round(train_rmse, 2),
        'Test RMSE (₹)': round(test_rmse, 2),
        'Train R²': round(train_r2, 4),
        'Test R²': round(test_r2, 4)
    })
    
    print(f"[{name}] Test MAE: INR {test_mae:.2f} | Test RMSE: INR {test_rmse:.2f} | Test R2: {test_r2:.4f}")

df_results = pd.DataFrame(results)
print("\n=== FINAL MODEL PERFORMANCE SUMMARY ===")
print(df_results.to_markdown(index=False))

# Export metrics
df_results.to_csv(os.path.join(REPORTS_DIR, "model_evaluation_metrics.csv"), index=False)
with open(os.path.join(REPORTS_DIR, "model_evaluation_metrics.md"), "w", encoding="utf-8") as f:
    f.write("# Machine Learning Model Evaluation & Benchmark Summary\n\n")
    f.write(df_results.to_markdown(index=False) + "\n\n")
    f.write("### Evaluation Criteria:\n")
    f.write("- **MAE (Mean Absolute Error)**: Average absolute magnitude of error in INR.\n")
    f.write("- **MSE (Mean Squared Error)** / **RMSE**: Penalizes large deviations, measuring standard error.\n")
    f.write("- **R² Score**: Proportion of variance in retail order values explained by the model.\n")

# ------------------------------------------------------------------------------
# 5. Champion Model Analysis & Artifact Export
# ------------------------------------------------------------------------------
champion_name = 'Random Forest Regressor (Tuned)'
champion_pipe = fitted_pipelines[champion_name]

# Save pipeline artifact
model_path = os.path.join(MODELS_DIR, "retail_sales_rf_model.joblib")
joblib.dump(champion_pipe, model_path)
print(f"\n[INFO] Champion model saved to {model_path}")

# Feature Importance extraction
ohe = champion_pipe.named_steps['preprocessor'].named_transformers_['cat']
cat_feature_names = ohe.get_feature_names_out(categorical_cols).tolist()
all_feature_names = numerical_cols + cat_feature_names

rf_model = champion_pipe.named_steps['regressor']
importances = rf_model.feature_importances_
df_imp = pd.DataFrame({
    'Feature': all_feature_names,
    'Importance': importances
}).sort_values('Importance', ascending=False)

df_imp.to_csv(os.path.join(REPORTS_DIR, "feature_importances.csv"), index=False)

# Plot Feature Importance (Top 15)
print("[INFO] Generating 09_rf_feature_importance.png...")
plt.figure(figsize=(10, 6.5))
top_imp = df_imp.head(15).iloc[::-1]
plt.barh(top_imp['Feature'], top_imp['Importance'], color='#3B82F6', height=0.65)
plt.title('Top 15 Most Influential Features (Random Forest Regressor)', fontsize=13, fontweight='bold', pad=15)
plt.xlabel('Gini Importance (MDI)', fontsize=11, fontweight='bold')
for idx, (val, feat) in enumerate(zip(top_imp['Importance'], top_imp['Feature'])):
    plt.text(val + 0.005, idx, f"{val:.3f}", va='center', fontsize=9, fontweight='semibold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '09_rf_feature_importance.png'), dpi=300)
plt.close()

# ------------------------------------------------------------------------------
# 6. Actual vs Predicted Plots & Residual Analysis
# ------------------------------------------------------------------------------
print("[INFO] Generating 10_actual_vs_predicted_sales.png...")
y_test_pred = champion_pipe.predict(X_test)
residuals = y_test - y_test_pred

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Actual vs Predicted Scatter
axes[0].scatter(y_test, y_test_pred, alpha=0.5, color='#2563EB', edgecolors='none', s=30)
max_val = max(y_test.max(), y_test_pred.max())
axes[0].plot([0, max_val], [0, max_val], 'r--', lw=2, label='Perfect Prediction Line')
axes[0].set_xlabel('Actual Order Value (₹ INR)', fontsize=11, fontweight='bold')
axes[0].set_ylabel('Predicted Order Value (₹ INR)', fontsize=11, fontweight='bold')
axes[0].set_title(f'Actual vs. Predicted Sales (Test R² = {df_results.loc[df_results["Model"]==champion_name, "Test R²"].values[0]})', fontsize=12, fontweight='bold')
axes[0].legend()

# Residuals Distribution
sns.histplot(residuals, kde=True, ax=axes[1], color='#DC2626', bins=40)
axes[1].axvline(0, color='black', linestyle='--', lw=1.5)
axes[1].set_xlabel('Prediction Error / Residuals (₹ INR)', fontsize=11, fontweight='bold')
axes[1].set_ylabel('Frequency', fontsize=11, fontweight='bold')
axes[1].set_title(f'Residuals Distribution (Mean Error: ₹{residuals.mean():.2f})', fontsize=12, fontweight='bold')

plt.suptitle('Random Forest Regressor Performance Diagnostics', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, '10_actual_vs_predicted_sales.png'), dpi=300)
plt.close()

# Export test set predictions for Power BI and interactive dashboard
df_test_export = X_test.copy()
df_test_export['Actual_Order_Value_INR'] = y_test.values
df_test_export['Predicted_Order_Value_INR'] = np.round(y_test_pred, 2)
df_test_export['Residual_INR'] = np.round(residuals.values, 2)
df_test_export['Abs_Pct_Error'] = np.round(np.abs(residuals.values) / y_test.values * 100, 2)
df_test_export.to_csv(os.path.join(BASE_DIR, "data", "test_predictions.csv"), index=False)
print(f"[INFO] Exported test predictions ({len(df_test_export)} rows) to data/test_predictions.csv")

print("[SUCCESS] Stage 3: Feature Engineering & Machine Learning pipeline completed successfully.")
