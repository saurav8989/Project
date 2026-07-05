import os
import sys
import warnings
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

warnings.filterwarnings('ignore')

# Add project root and thesis script directories to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(current_dir))

# Import shared Data Prep engine
from predictive_modeling import ImmunizationDataPrep

TABLES_DIR = project_root / "thesis" / "outputs" / "tables"
MODELS_ROOT = project_root / "thesis" / "outputs" / "models" / "Residual_Based_Hybrid"

# Subdirectories for model serialization
SUBDIRS = {
    'ARIMA_RF': MODELS_ROOT / "ARIMA_RF",
    'SARIMA_GB': MODELS_ROOT / "SARIMA_GB",
    'Prophet_RF': MODELS_ROOT / "Prophet_RF",
    'SARIMA_Prophet': MODELS_ROOT / "SARIMA_Prophet"
}

# Ensure subdirectories exist
for name, path in SUBDIRS.items():
    os.makedirs(path, exist_ok=True)

def fit_residual_hybrid_models(suffix="cleaned"):
    print(f"\n==================================================")
    print(f"RUNNING RESIDUAL HYBRID FORECASTING: {suffix.upper()}")
    print(f"==================================================")
    
    raw_csv = TABLES_DIR / "Indicators_Raw.csv"
    cleaned_csv = TABLES_DIR / "Indicators_Cleaned.csv"
    prep = ImmunizationDataPrep(raw_csv, cleaned_csv)
    
    # Load ADF report to get differencing orders
    adf_report_path = TABLES_DIR / "adf_stationarity_report.csv"
    if adf_report_path.exists():
        adf_report_df = pd.read_csv(adf_report_path)
    else:
        adf_report_df = None

    indicators = [col for col in prep.df_cleaned.columns if col.endswith('_Coverage') or col.endswith('_Dropout')]
    
    all_predictions = []
    all_metrics = []
    
    for idx, col in enumerate(indicators):
        print(f"[{idx+1}/{len(indicators)}] Modeling {col}...")
        
        # 1. Load splits
        train_y, test_y = prep.prepare_univariate_split(suffix, col)
        X_train, X_test, y_train, y_test = prep.prepare_ml_features(suffix, col)
        
        # Fetch differencing order d
        d_val = 1
        if adf_report_df is not None:
            match_row = adf_report_df[adf_report_df['Indicator'] == col]
            if not match_row.empty:
                col_prefix = suffix.capitalize()
                d_str = str(match_row.iloc[0][f'{col_prefix}_Required_d'])
                d_val = 0 if d_str == '0' else 1
        
        # -------------------------------------------------------------
        # MODEL 1: ARIMA-RF (ARIMA + RF)
        # -------------------------------------------------------------
        arima_fc = np.zeros(12)
        arima_rf_fc = np.zeros(12)
        try:
            # Stage 1: Fit ARIMA
            arima_model = ARIMA(train_y, order=(1, d_val, 1))
            arima_fit = arima_model.fit()
            arima_fc = arima_fit.forecast(steps=12).values
            
            # Compute train residuals
            arima_resid_train = train_y - arima_fit.fittedvalues
            
            # Align residual targets to ML training features
            y_resid_train = arima_resid_train.loc[X_train.index]
            
            # Stage 2: Train Random Forest Regressor on residuals
            rf_resid = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
            rf_resid.fit(X_train, y_resid_train)
            
            # Predict out-of-sample residuals
            predicted_resid = rf_resid.predict(X_test)
            
            # Combine forecast
            arima_rf_fc = arima_fc + predicted_resid
            
            # Serialize RF corrector
            joblib.dump(rf_resid, SUBDIRS['ARIMA_RF'] / f"{col}_rf_resid.joblib")
            
        except Exception as e:
            print(f"  ❌ ARIMA-RF failed: {e}")
            arima_rf_fc = arima_fc # Fallback to Stage-1
            
        # -------------------------------------------------------------
        # MODEL 2: SARIMA-GB (SARIMA + GB)
        # -------------------------------------------------------------
        sarima_fc = np.zeros(12)
        sarima_gb_fc = np.zeros(12)
        try:
            # Stage 1: Fit SARIMA
            sarima_model = SARIMAX(train_y, order=(1, d_val, 1), seasonal_order=(0, d_val, 0, 12))
            sarima_fit = sarima_model.fit(disp=False)
            sarima_fc = sarima_fit.forecast(steps=12).values
            
            # Compute train residuals
            sarima_resid_train = train_y - sarima_fit.fittedvalues
            y_resid_train = sarima_resid_train.loc[X_train.index]
            
            # Stage 2: Train Gradient Boosting on residuals
            gb_resid = GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42)
            gb_resid.fit(X_train, y_resid_train)
            
            predicted_resid = gb_resid.predict(X_test)
            sarima_gb_fc = sarima_fc + predicted_resid
            
            # Serialize GB corrector
            joblib.dump(gb_resid, SUBDIRS['SARIMA_GB'] / f"{col}_gb_resid.joblib")
            
        except Exception as e:
            print(f"  ❌ SARIMA-GB failed: {e}")
            sarima_gb_fc = sarima_fc
            
        # -------------------------------------------------------------
        # MODEL 3: Prophet-RF (Prophet + RF)
        # -------------------------------------------------------------
        prophet_fc = np.zeros(12)
        prophet_rf_fc = np.zeros(12)
        try:
            # Stage 1: Fit Prophet
            train_df = pd.DataFrame({
                'ds': train_y.index.tz_localize(None),
                'y': train_y.values
            })
            prophet_model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            prophet_model.fit(train_df)
            
            # Generate in-sample and out-of-sample forecasts
            in_sample_pred = prophet_model.predict(train_df)['yhat'].values
            
            future_df = pd.DataFrame({'ds': test_y.index.tz_localize(None)})
            prophet_fc = prophet_model.predict(future_df)['yhat'].values
            
            # Compute train residuals
            prophet_resid_train = train_y.values - in_sample_pred
            prophet_resid_train_series = pd.Series(prophet_resid_train, index=train_y.index)
            y_resid_train = prophet_resid_train_series.loc[X_train.index]
            
            # Stage 2: Train RF corrector on residuals
            rf_resid_prophet = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
            rf_resid_prophet.fit(X_train, y_resid_train)
            
            predicted_resid = rf_resid_prophet.predict(X_test)
            prophet_rf_fc = prophet_fc + predicted_resid
            
            # Serialize RF corrector
            joblib.dump(rf_resid_prophet, SUBDIRS['Prophet_RF'] / f"{col}_rf_resid.joblib")
            
        except Exception as e:
            print(f"  ❌ Prophet-RF failed: {e}")
            prophet_rf_fc = prophet_fc
            
        # -------------------------------------------------------------
        # MODEL 4: SARIMA-Prophet (SARIMA + Prophet)
        # -------------------------------------------------------------
        sarima_prophet_fc = np.zeros(12)
        try:
            # We already have sarima_fc and sarima_resid_train from MODEL 2
            # Stage 2: Train Prophet on SARIMA residuals
            resid_df = pd.DataFrame({
                'ds': train_y.index.tz_localize(None),
                'y': sarima_resid_train.values
            })
            prophet_corrector = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            prophet_corrector.fit(resid_df)
            
            future_df = pd.DataFrame({'ds': test_y.index.tz_localize(None)})
            predicted_resid = prophet_corrector.predict(future_df)['yhat'].values
            
            sarima_prophet_fc = sarima_fc + predicted_resid
            
            # Serialize Prophet corrector
            joblib.dump(prophet_corrector, SUBDIRS['SARIMA_Prophet'] / f"{col}_prophet_resid.joblib")
            
        except Exception as e:
            print(f"  ❌ SARIMA-Prophet failed: {e}")
            sarima_prophet_fc = sarima_fc
            
        # -------------------------------------------------------------
        # POST-PROCESSING: CLINICAL CAPPING RULES
        # -------------------------------------------------------------
        is_coverage = col.endswith('_Coverage')
        
        def cap_forecast(arr):
            if is_coverage:
                return np.clip(arr, 0.0, 100.0)
            else:
                return np.clip(arr, 0.0, None)
                
        arima_rf_fc = cap_forecast(arima_rf_fc)
        sarima_gb_fc = cap_forecast(sarima_gb_fc)
        prophet_rf_fc = cap_forecast(prophet_rf_fc)
        sarima_prophet_fc = cap_forecast(sarima_prophet_fc)
        
        # -------------------------------------------------------------
        # SAVE PREDICTIONS & COMPUTE METRICS
        # -------------------------------------------------------------
        pred_df = pd.DataFrame({
            'Indicator': col,
            'Fiscal Year': '2081/82',
            'Month No.': range(49, 61),
            'Month (EN)': ['Shrawan', 'Bhadra', 'Ashwin', 'Kartik', 'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra', 'Baishak', 'Jestha', 'Asar'],
            'Month (NP)': ['Sawan', 'Bhadau', 'Asoj', 'Kattik', 'Mangsir', 'Pus', 'Magh', 'Fagun', 'Chait', 'Baisakh', 'Jeth', 'Asar'],
            'Actual': test_y.values,
            'ARIMA_RF_Forecast': arima_rf_fc,
            'SARIMA_GB_Forecast': sarima_gb_fc,
            'Prophet_RF_Forecast': prophet_rf_fc,
            'SARIMA_Prophet_Forecast': sarima_prophet_fc
        })
        all_predictions.append(pred_df)
        
        # Calculate metrics for each combination
        actuals = test_y.values
        mask = ~np.isnan(actuals)
        
        metrics_dict = {'Indicator': col}
        for model_name, preds in [('ARIMA_RF', arima_rf_fc), ('SARIMA_GB', sarima_gb_fc), ('Prophet_RF', prophet_rf_fc), ('SARIMA_Prophet', sarima_prophet_fc)]:
            if mask.sum() > 0:
                mae = np.mean(np.abs(actuals[mask] - preds[mask]))
                rmse = np.sqrt(np.mean((actuals[mask] - preds[mask]) ** 2))
                # MAPE
                actuals_mape = actuals[mask]
                preds_mape = preds[mask]
                mape_mask = actuals_mape != 0
                mape = np.mean(np.abs((actuals_mape[mape_mask] - preds_mape[mape_mask]) / actuals_mape[mape_mask])) * 100.0 if mape_mask.sum() > 0 else 0.0
            else:
                mae, rmse, mape = 0.0, 0.0, 0.0
                
            metrics_dict[f'{model_name}_MAE'] = mae
            metrics_dict[f'{model_name}_RMSE'] = rmse
            metrics_dict[f'{model_name}_MAPE'] = mape
            
        all_metrics.append(metrics_dict)
        
    # Write files
    if all_predictions:
        pd.concat(all_predictions, ignore_index=True).to_csv(TABLES_DIR / f"predictions_residual_hybrid_{suffix}.csv", index=False)
        pd.DataFrame(all_metrics).to_csv(TABLES_DIR / f"metrics_residual_hybrid_{suffix}.csv", index=False)
        print(f"✅ Generated predictions and metrics for: residual_hybrid_{suffix}")

if __name__ == "__main__":
    fit_residual_hybrid_models("cleaned")
    fit_residual_hybrid_models("raw")
    print("\n✅ RESIDUAL HYBRID FORECASTING PIPELINE COMPLETED")
