import os
import sys
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

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

def run_ml_pipeline(prep, dataset_type, output_dir):
    """
    Runs the grid search, fitting, and evaluation loops for RF and GB Regressors
    on all 24 indicators.
    """
    print(f"\n--- Running ML Regression Pipeline on {dataset_type.upper()} Dataset ---")
    
    # Identify indicators dynamically
    indicators = [col for col in prep.df_cleaned.columns if col.endswith('_Coverage') or col.endswith('_Dropout')]
    
    metrics_records = []
    predictions_records = []
    
    # Hyperparameter grids
    rf_param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [3, 5, None],
        'min_samples_split': [2, 5]
    }
    
    gb_param_grid = {
        'n_estimators': [50, 100],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [3, 4]
    }
    
    for idx, col in enumerate(indicators):
        print(f"[{idx+1}/{len(indicators)}] Modeling {col} with RF and GB...")
        
        # Get ML feature splits
        X_train, X_test, y_train, y_test = prep.prepare_ml_features(dataset_type, col)
        
        if len(X_train) < 10:
            print(f"⚠️ Skipping {col} (insufficient data: {len(X_train)} samples)")
            continue
            
        # Determine CV splits dynamically to prevent crashes on short datasets (like TCV)
        n_splits = min(3, len(X_train) // 5)
        n_splits = max(2, n_splits) # Minimum of 2 splits
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        # 1. Random Forest Regressor Grid Search
        rf_model = RandomForestRegressor(random_state=42)
        rf_grid = GridSearchCV(estimator=rf_model, param_grid=rf_param_grid, cv=tscv, scoring='neg_mean_squared_error', n_jobs=-1)
        
        try:
            rf_grid.fit(X_train, y_train)
            best_rf = rf_grid.best_estimator_
            rf_forecast = best_rf.predict(X_test)
            
            # Post-processing boundaries
            if col.endswith('_Coverage'):
                rf_forecast = np.clip(rf_forecast, 0.0, 100.0)
            elif col.endswith('_Dropout'):
                rf_forecast = np.maximum(rf_forecast, 0.0)
                
            rf_mae, rf_rmse, rf_mape = evaluate_predictions(y_test.values, rf_forecast)
            best_rf_params = str(rf_grid.best_params_)
        except Exception as e:
            print(f"❌ RF failed on {col}: {e}")
            rf_forecast = np.full(len(y_test), np.nan)
            rf_mae, rf_rmse, rf_mape = np.nan, np.nan, np.nan
            best_rf_params = "Failed"
            
        # 2. Gradient Boosting Regressor Grid Search
        gb_model = GradientBoostingRegressor(random_state=42)
        gb_grid = GridSearchCV(estimator=gb_model, param_grid=gb_param_grid, cv=tscv, scoring='neg_mean_squared_error', n_jobs=-1)
        
        try:
            gb_grid.fit(X_train, y_train)
            best_gb = gb_grid.best_estimator_
            gb_forecast = best_gb.predict(X_test)
            
            # Post-processing boundaries
            if col.endswith('_Coverage'):
                gb_forecast = np.clip(gb_forecast, 0.0, 100.0)
            elif col.endswith('_Dropout'):
                gb_forecast = np.maximum(gb_forecast, 0.0)
                
            gb_mae, gb_rmse, gb_mape = evaluate_predictions(y_test.values, gb_forecast)
            best_gb_params = str(gb_grid.best_params_)
        except Exception as e:
            print(f"❌ GB failed on {col}: {e}")
            gb_forecast = np.full(len(y_test), np.nan)
            gb_mae, gb_rmse, gb_mape = np.nan, np.nan, np.nan
            best_gb_params = "Failed"
            
        # 3. Append metrics
        metrics_records.append({
            'Indicator': col,
            'RF_Params': best_rf_params,
            'RF_MAE': rf_mae,
            'RF_RMSE': rf_rmse,
            'RF_MAPE': rf_mape,
            'GB_Params': best_gb_params,
            'GB_MAE': gb_mae,
            'GB_RMSE': gb_rmse,
            'GB_MAPE': gb_mape
        })
        
        # 4. Append forecasts for each month in y_test, mapping back to original Nepali calendar fields
        df_meta = prep.df_cleaned if dataset_type == 'cleaned' else prep.df_raw
        for idx_t, date in enumerate(y_test.index):
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
                'Actual': y_test.iloc[idx_t],
                'RF_Forecast': rf_forecast[idx_t],
                'GB_Forecast': gb_forecast[idx_t]
            })
            
    # Save files to workspace
    metrics_df = pd.DataFrame(metrics_records)
    predictions_df = pd.DataFrame(predictions_records)
    
    metrics_path = output_dir / "Metrics" / f"metrics_ml_{dataset_type}.csv"
    predictions_path = output_dir / "Predictions" / f"predictions_ml_{dataset_type}.csv"
    
    metrics_df.to_csv(metrics_path, index=False)
    predictions_df.to_csv(predictions_path, index=False)
    
    print(f"✅ Saved metrics to: {metrics_path}")
    print(f"✅ Saved forecasts to: {predictions_path}")
    
    # Print summary averages
    print(f"Average RF RMSE on {dataset_type}: {metrics_df['RF_RMSE'].mean():.4f}")
    print(f"Average GB RMSE on {dataset_type}: {metrics_df['GB_RMSE'].mean():.4f}")

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4 - STEP 4.4: ML REGRESSION FORECASTING PIPELINE")
    print("=" * 60)
    
    # Paths
    raw_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Raw.csv"
    cleaned_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Cleaned.csv"
    tables_dir = project_root / "thesis" / "outputs" / "tables"
    
    prep = ImmunizationDataPrep(raw_csv, cleaned_csv)
    
    # Run pipeline for both Raw and Cleaned
    run_ml_pipeline(prep, 'raw', tables_dir)
    run_ml_pipeline(prep, 'cleaned', tables_dir)
    
    print("\n✅ STEP 4.4 COMPLETE")
    print("=" * 60)
