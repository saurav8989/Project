import os
import sys
import pandas as pd
import numpy as np
import warnings
import logging
from pathlib import Path
from prophet import Prophet

# Suppress Prophet and cmdstanpy diagnostic logging
logging.getLogger('prophet').setLevel(logging.WARNING)
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
warnings.filterwarnings('ignore')

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

def evaluate_predictions(y_true, y_pred):
    """
    Computes regression error metrics.
    """
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mape = calculate_mape(y_true, y_pred)
    return mae, rmse, mape

def run_prophet_pipeline(prep, dataset_type, output_dir):
    """
    Runs the fitting and evaluation loops for the Prophet forecasting model
    on all 24 indicators.
    """
    print(f"\n--- Running Prophet Pipeline on {dataset_type.upper()} Dataset ---")
    
    # Identify indicators dynamically
    indicators = [col for col in prep.df_cleaned.columns if col.endswith('_Coverage') or col.endswith('_Dropout')]
    
    metrics_records = []
    predictions_records = []
    
    for idx, col in enumerate(indicators):
        print(f"[{idx+1}/{len(indicators)}] Modeling {col} with Prophet...")
        
        # Get univariate train/test sets
        train_y, test_y = prep.prepare_univariate_split(dataset_type, col)
        
        if len(train_y) < 10:
            print(f"⚠️ Skipping {col} (insufficient data: {len(train_y)} months)")
            continue
            
        # 1. Format to Prophet structure: ds and y
        df_train = pd.DataFrame({
            'ds': train_y.index.tz_localize(None), # Ensure timezone naive
            'y': train_y.values
        })
        
        df_future = pd.DataFrame({
            'ds': test_y.index.tz_localize(None)
        })
        
        # 2. Fit Prophet model
        try:
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False
            )
            model.fit(df_train)
            
            # Predict
            forecast = model.predict(df_future)
            forecast_y = forecast['yhat'].values
            
            # 3. Post-processing: Apply boundary capping/smoothing rules
            if col.endswith('_Coverage'):
                forecast_y = np.clip(forecast_y, 0.0, 100.0)
            elif col.endswith('_Dropout'):
                forecast_y = np.maximum(forecast_y, 0.0)
                
        except Exception as e:
            print(f"❌ Prophet failed to fit on {col}: {e}")
            forecast_y = np.full(len(test_y), np.nan)
            
        # 4. Calculate metrics
        if not np.isnan(forecast_y[0]):
            mae, rmse, mape = evaluate_predictions(test_y.values, forecast_y)
        else:
            mae, rmse, mape = np.nan, np.nan, np.nan
            
        # Append metrics
        metrics_records.append({
            'Indicator': col,
            'Prophet_MAE': mae,
            'Prophet_RMSE': rmse,
            'Prophet_MAPE': mape
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
                'Prophet_Forecast': forecast_y[idx_t]
            })
            
    # Save files to workspace
    metrics_df = pd.DataFrame(metrics_records)
    predictions_df = pd.DataFrame(predictions_records)
    
    metrics_path = output_dir / "Metrics" / f"metrics_prophet_{dataset_type}.csv"
    predictions_path = output_dir / "Predictions" / f"predictions_prophet_{dataset_type}.csv"
    
    metrics_df.to_csv(metrics_path, index=False)
    predictions_df.to_csv(predictions_path, index=False)
    
    print(f"✅ Saved metrics to: {metrics_path}")
    print(f"✅ Saved forecasts to: {predictions_path}")
    
    # Print summary averages
    print(f"Average Prophet RMSE on {dataset_type}: {metrics_df['Prophet_RMSE'].mean():.4f}")

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4 - STEP 4.3: PROPHET BAYESIAN FORECASTING PIPELINE")
    print("=" * 60)
    
    # Paths
    raw_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Raw.csv"
    cleaned_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Cleaned.csv"
    tables_dir = project_root / "thesis" / "outputs" / "tables"
    
    prep = ImmunizationDataPrep(raw_csv, cleaned_csv)
    
    # Run pipeline for both Raw and Cleaned
    run_prophet_pipeline(prep, 'raw', tables_dir)
    run_prophet_pipeline(prep, 'cleaned', tables_dir)
    
    print("\n✅ STEP 4.3 COMPLETE")
    print("=" * 60)
