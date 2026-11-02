# Machine Learning Model Evaluation & Benchmark Summary

| Model                           |   Train MAE (₹) |   Test MAE (₹) |   Train RMSE (₹) |   Test RMSE (₹) |   Train R² |   Test R² |
|:--------------------------------|----------------:|---------------:|-----------------:|----------------:|-----------:|----------:|
| Dummy Regressor (Mean)          |         7893.28 |        7932.87 |         12232    |        12361.5  |     0      |   -0      |
| Linear Regression               |         3123.43 |        3233.34 |          5082.69 |         5300.06 |     0.8273 |    0.8162 |
| Ridge Regression (alpha=1.0)    |         3122.98 |        3233.04 |          5082.75 |         5300.9  |     0.8273 |    0.8161 |
| Decision Tree Regressor         |         1303.21 |        3691.37 |          2601.34 |         6831.18 |     0.9548 |    0.6946 |
| Random Forest Regressor (Tuned) |         1393.29 |        3053.7  |          2305.2  |         5273.1  |     0.9645 |    0.818  |

### Evaluation Criteria:
- **MAE (Mean Absolute Error)**: Average absolute magnitude of error in INR.
- **MSE (Mean Squared Error)** / **RMSE**: Penalizes large deviations, measuring standard error.
- **R² Score**: Proportion of variance in retail order values explained by the model.
