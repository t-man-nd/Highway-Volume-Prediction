# Highway Traffic Volume Forecasting: A Comparative Approach from SARIMA to XGBoost

This repository hosts an end-to-end data science pipeline for extracting, preprocessing, analyzing, and forecasting highway traffic volume. Focusing on target station **3-026** using historical records spanning from 2015 to 2023, the project evaluates and compares classical statistical frameworks (SARIMA, Holt-Winters) against modern machine learning approaches (XGBoost) for monthly time-series forecasting.

---
Course: Timeseries Analysis

Student Name: Ninh Duy Tuân

Class: DSEB 65B

StudentID: 11230598

---
## 🚀 Project Pipeline & Core Features

### 1. Automated ETL & Data Extraction (`extract.py`)
* **Multi-Year Consolidation:** Parses raw, distributed annual Excel workbooks (`{year}-raw-data.xlsx`) to discover and extract sheets containing "Daily Traffic Summary" reports.
* **Structural Cleaning:** Automatically purges annual average metrics, aggregate row estimates, or non-date rows (such as Annual Average Daily Traffic - $\text{AADT}$) to isolate pure historical observations.
* **Standardization:** Standardizes dates into 64-bit datetime points (`datetime64[ns]`) and saves the clean sub-tables to standard CSV files under the `extracted-sheets/` directory.

### 2. Chronological Continuity & Gap Detection
* Since rigorous time-series models (like SARIMA) require an absolute unbroken calendar axis, the pipeline uses a reference `pd.date_range`.
* By computing index set differences (`.difference()`), the system automatically flags missing historical dates (e.g., `2016-08-31`), reindexes the dataset, and properly patches them with `NaN` placeholders before smoothing.

### 3. Leakage-Free Preprocessing & Outlier Mitigation
To preserve statistical integrity and strictly block **Data Leakage** or **Look-ahead Bias**, the pipeline isolates the Train set (2015–2022, 96 months) from the Test set (2023, 12 months):
* **Train Set Adjustments:** Unrealistic anomalies—such as zero traffic counts (sensor failures) or extreme values exceeding `10,000 vehicles/day`—are masked as `NaN` and smoothed using localized linear interpolation (`.interpolate(method='linear')`).
* **Test Set Safeguards:** For any missing entries within the 2023 evaluation partition, the system anchors the edge calculation exclusively on the final real training element (`last_train_val`), avoiding forward-looking imputation dependencies.

### 4. Statistical Analysis & Stationarity Testing
* **Augmented Dickey-Fuller (ADF) Test:** Evaluates the stationarity profile of the data through variance and mean differences.
* **ACF & PACF Diagnostics:** Computes and plots Autocorrelation and Partial Autocorrelation graphs on natural and seasonal difference levels ($d=1, D=1$) to establish parameter bounds ($p, q, P, Q$) for modeling.

### 5. Multi-Model Forecasting Framework
The predictive pipeline integrates and benchmarks multiple algorithmic families:
* **Statistical Benchmarks:** Multi-factor Holt-Winters Exponential Smoothing and comprehensive SARIMAX modeling.
* **Machine Learning:** Non-linear regression using an engineered `XGBoost Regressor` architecture.
* **Metrics:** Model performances are assessed via Standard Mean Squared Error (MSE), Root Mean Squared Error (RMSE), and Mean Absolute Error (MAE).

---

## 🛠️ Tech Stack & Dependencies

* **Language:** Python 3.x
* **Core Libraries:**
  * **Data Wrangling:** `pandas`, `numpy`, `openpyxl`
  * **Visualization:** `matplotlib`, `seaborn`
  * **Statistical Modeling:** `statsmodels` (ADF test, ACF/PACF plots, SARIMAX, ExponentialSmoothing)
  * **Machine Learning:** `xgboost`, `scikit-learn`

---

## 📦 Installation & Getting Started

### 1. Setup Environment
Clone the repository and install all required python dependencies:
```bash
git clone [https://github.com/t-man-nd/Highway-Volume-Prediction.git](https://github.com/t-man-nd/Highway-Volume-Prediction.git)
cd Highway-Volume-Prediction
pip install -r requirements.txt
