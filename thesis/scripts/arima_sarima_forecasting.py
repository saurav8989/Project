import os
import sys
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# Suppress warnings from statsmodels optimization loops
warnings.filterwarnings('ignore', category=ConvergenceWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Add project root and script directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(current_dir))

# Import shared Data Prep engine from Step 4.1
from predictive_modeling import ImmunizationDataPrep

def calculate_mape(y_true, y_pred):
    """
    Safely calculates Mean Absolute Percentage Error (MAPE)
    by ignoring elements where the true value is 0.0.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    non_zero_mask = y_true != 0.0
    if not np.any(non_zero_mask):
        return 0.0
    return np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100.0

def grid_search_arima(train_y, d_order):
    """
    Grid searches ARIMA(p, d, q) parameters to minimize AIC.
    """
    best_aic = float('inf')
    best_order = (0, d_order, 0)
    
    for p in [0, 1, 2]:
        for q in [0, 1, 2]:
            try:
                model = ARIMA(train_y, order=(p, d_order, q))
                results = model.fit()
                if results.aic < best_aic:
                    best_aic = results.aic
                    best_order = (p, d_order, q)
            except Exception:
                continue
    return best_order

def grid_search_sarima(train_y, d_order):
    """
    Grid searches SARIMA(p, d, q)x(P, D, Q)_12 parameters to minimize AIC.
    Ties seasonal D to non-seasonal d to stabilize convergence.
    """
    best_aic = float('inf')
    best_order = (1, d_order, 1)
    best_seasonal_order = (0, d_order, 0, 12)
    
    for p in [0, 1, 2]:
        for q in [0, 1, 2]:
            for P in [0, 1]:
                for Q in [0, 1]:
                    try:
                        model = SARIMAX(
                            train_y,
                            order=(p, d_order, q),
                            seasonal_order=(P, d_order, Q, 12),
                            enforce_stationarity=False,
                            enforce_invertibility=False
                        )
                        results = model.fit(disp=False)
                        if results.aic < best_aic:
                            best_aic = results.aic
                            best_order = (p, d_order, q)
                            best_seasonal_order = (P, d_order, Q, 12)
                    except Exception:
                        continue
    return best_order, best_seasonal_order

def evaluate_predictions(y_true, y_pred):
    """
    Computes regression error metrics.
    """
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mape = calculate_mape(y_true, y_pred)
    return mae, rmse, mape

def run_arima_sarima_pipeline(prep, dataset_type, adf_report_df, output_dir):
    """
    Runs the grid search, fitting, and evaluation loops for ARIMA and SARIMA
    on all 24 indicators.
    """
    print(f"\n--- Running ARIMA/SARIMA Pipeline on {dataset_type.upper()} Dataset ---")
    
    # Identify indicators dynamically from columns (excluding non-numeric/metadata)
    indicators = [col for col in prep.df_cleaned.columns if col.endswith('_Coverage') or col.endswith('_Dropout')]
    
    metrics_records = []
    predictions_records = []
    
    for idx, col in enumerate(indicators):
        print(f"[{idx+1}/{len(indicators)}] Modeling {col}...")
        
        # Get univariate train/test sets (with TCV pre-introduction exclusion applied)
        train_y, test_y = prep.prepare_univariate_split(dataset_type, col)
        
        if len(train_y) < 10:
            print(f"⚠️ Skipping {col} (insufficient data: {len(train_y)} months)")
            continue
            
        # 1. Fetch differencing order d from Phase 3 ADF report
        # If not found or invalid, default to 1.
        d_val = 1
        col_type = "Raw_Required_d" if dataset_type == 'raw' else "Cleaned_Required_d"
        match_row = adf_report_df[adf_report_df['Indicator'] == col]
        if not match_row.empty:
            d_str = str(match_row.iloc[0][col_type])
            d_val = 0 if d_str == '0' else 1
            
        # 2. Fit ARIMA
        best_arima_order = grid_search_arima(train_y, d_val)
        try:
            arima_model = ARIMA(train_y, order=best_arima_order)
            arima_res = arima_model.fit()
            arima_forecast = arima_res.forecast(steps=len(test_y))
            # Handle float alignments in predictions
            arima_forecast = np.array(arima_forecast)
        except Exception as e:
            print(f"❌ ARIMA failed to fit on {col}: {e}")
            arima_forecast = np.full(len(test_y), np.nan)
            best_arima_order = (np.nan, np.nan, np.nan)
            
        # 3. Fit SARIMA
        best_sarima_order, best_seasonal_order = grid_search_sarima(train_y, d_val)
        try:
            sarima_model = SARIMAX(
                train_y,
                order=best_sarima_order,
                seasonal_order=best_seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            sarima_res = sarima_model.fit(disp=False)
            sarima_forecast = sarima_res.forecast(steps=len(test_y))
            sarima_forecast = np.array(sarima_forecast)
        except Exception as e:
            print(f"❌ SARIMA failed to fit on {col}: {e}")
            sarima_forecast = np.full(len(test_y), np.nan)
            best_sarima_order = (np.nan, np.nan, np.nan)
            best_seasonal_order = (np.nan, np.nan, np.nan, 12)
            
        # 4. Calculate metrics
        # If fit failed, set metrics to NaN
        if not np.isnan(arima_forecast[0]):
            arima_mae, arima_rmse, arima_mape = evaluate_predictions(test_y.values, arima_forecast)
        else:
            arima_mae, arima_rmse, arima_mape = np.nan, np.nan, np.nan
            
        if not np.isnan(sarima_forecast[0]):
            sarima_mae, sarima_rmse, sarima_mape = evaluate_predictions(test_y.values, sarima_forecast)
        else:
            sarima_mae, sarima_rmse, sarima_mape = np.nan, np.nan, np.nan
            
        # Append metrics
        metrics_records.append({
            'Indicator': col,
            'ARIMA_Order': str(best_arima_order),
            'ARIMA_MAE': arima_mae,
            'ARIMA_RMSE': arima_rmse,
            'ARIMA_MAPE': arima_mape,
            'SARIMA_Order': f"{best_sarima_order}x{best_seasonal_order}",
            'SARIMA_MAE': sarima_mae,
            'SARIMA_RMSE': sarima_rmse,
            'SARIMA_MAPE': sarima_mape
        })
        
        # Append forecasts for each month in test_y, mapping back to original Nepali calendar fields
        df_meta = prep.df_cleaned if dataset_type == 'cleaned' else prep.df_raw
        for idx_t, date in enumerate(test_y.index):
            row_meta = df_meta.loc[date]
            fiscal_year = row_meta['Fiscal Year']
            month_no = row_meta['Month No.']
            month_en = row_meta['Month (EN)']
            month_np = row_meta['Month (NP)']
            
            predictions_records.append({
                'Indicator': col,
                'Fiscal Year': fiscal_year,
                'Month No.': month_no,
                'Month (EN)': month_en,
                'Month (NP)': month_np,
                'Actual': test_y.iloc[idx_t],
                'ARIMA_Forecast': arima_forecast[idx_t],
                'SARIMA_Forecast': sarima_forecast[idx_t]
            })
            
    # Save files to workspace
    metrics_df = pd.DataFrame(metrics_records)
    predictions_df = pd.DataFrame(predictions_records)
    
    metrics_path = output_dir / "Metrics" / f"metrics_arima_sarima_{dataset_type}.csv"
    predictions_path = output_dir / "Predictions" / f"predictions_arima_sarima_{dataset_type}.csv"
    
    metrics_df.to_csv(metrics_path, index=False)
    predictions_df.to_csv(predictions_path, index=False)
    
    print(f"✅ Saved metrics to: {metrics_path}")
    print(f"✅ Saved forecasts to: {predictions_path}")
    
    # Print summary averages
    print(f"Average ARIMA RMSE  on {dataset_type}: {metrics_df['ARIMA_RMSE'].mean():.4f}")
    print(f"Average SARIMA RMSE on {dataset_type}: {metrics_df['SARIMA_RMSE'].mean():.4f}")

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4 - STEP 4.2: ARIMA & SARIMA FORECASTING PIPELINE")
    print("=" * 60)
    
    # Paths
    raw_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Raw.csv"
    cleaned_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Cleaned.csv"
    adf_csv = project_root / "thesis" / "outputs" / "tables" / "Diagnostics" / "adf_stationarity_comparison.csv"
    tables_dir = project_root / "thesis" / "outputs" / "tables"
    
    if adf_csv.exists():
        adf_df = pd.read_csv(adf_csv)
        prep = ImmunizationDataPrep(raw_csv, cleaned_csv)
        
        # Run pipeline for both Raw and Cleaned
        run_arima_sarima_pipeline(prep, 'raw', adf_df, tables_dir)
        run_arima_sarima_pipeline(prep, 'cleaned', adf_df, tables_dir)
    else:
        print("❌ Cannot run Step 4.2: adf_stationarity_comparison.csv not found in tables directory.")
        
    print("\n✅ STEP 4.2 COMPLETE")
    print("=" * 60)
