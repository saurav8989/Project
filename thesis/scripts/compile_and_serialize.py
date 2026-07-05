import os
import sys
import pandas as pd
import numpy as np
import warnings
import joblib
from pathlib import Path
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

warnings.filterwarnings('ignore')

# Add project root and script directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(current_dir))

# Import shared Data Prep engine from Step 4.1
from predictive_modeling import ImmunizationDataPrep

def compile_metrics(tables_dir):
    """
    Loads separate model metric files and aggregates them into master
    regression and classification comparative tables.
    """
    print("\n--- Compiling Master Evaluation Metrics Tables ---")
    
    # 1. REGRESSION METRICS COMPILATION
    datasets = ['raw', 'cleaned']
    reg_list = []
    
    for ds in datasets:
        arima_path = tables_dir / "Metrics" / f"metrics_arima_sarima_{ds}.csv"
        prophet_path = tables_dir / "Metrics" / f"metrics_prophet_{ds}.csv"
        ml_path = tables_dir / "Metrics" / f"metrics_ml_{ds}.csv"
        hybrid_path = tables_dir / "Metrics" / f"metrics_hybrid_{ds}.csv"
        residual_path = tables_dir / "Metrics" / f"metrics_residual_hybrid_{ds}.csv"
        
        if arima_path.exists() and prophet_path.exists() and ml_path.exists() and hybrid_path.exists() and residual_path.exists():
            df_arima = pd.read_csv(arima_path)
            df_prophet = pd.read_csv(prophet_path)
            df_ml = pd.read_csv(ml_path)
            df_hybrid = pd.read_csv(hybrid_path)
            df_residual = pd.read_csv(residual_path)
            
            # Merge on Indicator
            df_merge = pd.merge(df_arima, df_prophet, on='Indicator', how='outer')
            df_merge = pd.merge(df_merge, df_ml, on='Indicator', how='outer')
            df_merge = pd.merge(df_merge, df_hybrid, on='Indicator', how='outer')
            df_merge = pd.merge(df_merge, df_residual, on='Indicator', how='outer')
            
            # Select and rename key metrics for clean presentation
            df_summary = pd.DataFrame({
                'Indicator': df_merge['Indicator'],
                'Dataset': ds.capitalize(),
                'ARIMA_RMSE': df_merge['ARIMA_RMSE'],
                'SARIMA_RMSE': df_merge['SARIMA_RMSE'],
                'Prophet_RMSE': df_merge['Prophet_RMSE'],
                'RF_RMSE': df_merge['RF_RMSE'],
                'GB_RMSE': df_merge['GB_RMSE'],
                'Hybrid_RMSE': df_merge['Hybrid_RMSE'],
                'ARIMA_RF_RMSE': df_merge['ARIMA_RF_RMSE'],
                'SARIMA_GB_RMSE': df_merge['SARIMA_GB_RMSE'],
                'Prophet_RF_RMSE': df_merge['Prophet_RF_RMSE'],
                'SARIMA_Prophet_RMSE': df_merge['SARIMA_Prophet_RMSE'],
                'ARIMA_MAE': df_merge['ARIMA_MAE'],
                'SARIMA_MAE': df_merge['SARIMA_MAE'],
                'Prophet_MAE': df_merge['Prophet_MAE'],
                'RF_MAE': df_merge['RF_MAE'],
                'GB_MAE': df_merge['GB_MAE'],
                'Hybrid_MAE': df_merge['Hybrid_MAE'],
                'ARIMA_RF_MAE': df_merge['ARIMA_RF_MAE'],
                'SARIMA_GB_MAE': df_merge['SARIMA_GB_MAE'],
                'Prophet_RF_MAE': df_merge['Prophet_RF_MAE'],
                'SARIMA_Prophet_MAE': df_merge['SARIMA_Prophet_MAE']
            })
            reg_list.append(df_summary)
            
    if reg_list:
        reg_master = pd.concat(reg_list, ignore_index=True)
        reg_master_path = tables_dir / "Significance_Analysis" / "regression_summary.csv"
        reg_master.to_csv(reg_master_path, index=False)
        print(f"✅ Created master regression metrics summary: {reg_master_path}")
    else:
        print("⚠️ Could not compile regression metrics. Missing source files.")

    # 2. CLASSIFICATION METRICS COMPILATION
    class_list = []
    for ds in datasets:
        class_path = tables_dir / "Metrics" / f"metrics_classification_{ds}.csv"
        if class_path.exists():
            df_class = pd.read_csv(class_path)
            df_class.insert(1, 'Dataset', ds.capitalize())
            class_list.append(df_class)
            
    if class_list:
        class_master = pd.concat(class_list, ignore_index=True)
        class_master_path = tables_dir / "Significance_Analysis" / "classification_summary.csv"
        class_master.to_csv(class_master_path, index=False)
        print(f"✅ Created master classification metrics summary: {class_master_path}")
    else:
        print("⚠️ Could not compile classification metrics. Missing source files.")

def serialize_cleaned_models(prep, models_dir):
    """
    Fits ARIMA, SARIMA, Prophet, Random Forest, and Gradient Boosting models
    on the entire Cleaned dataset (all 60 months) and serializes them to disk.
    This prepares the final models for production forecasting of Year 6.
    """
    print("\n--- Serializing Production-Ready Models Trained on Entire Cleaned Dataset ---")
    
    # Define and create subdirectories for clean file organization
    subdirs = {
        'ARIMA': models_dir / "ARIMA",
        'SARIMA': models_dir / "SARIMA",
        'Prophet': models_dir / "Prophet",
        'RF': models_dir / "RF",
        'GB': models_dir / "GB"
    }
    for path in subdirs.values():
        os.makedirs(path, exist_ok=True)
    
    # Identify indicators dynamically
    indicators = [col for col in prep.df_cleaned.columns if col.endswith('_Coverage') or col.endswith('_Dropout')]
    
    # Load ADF report to get differencing orders
    adf_report_path = project_root / "thesis" / "outputs" / "tables" / "Diagnostics" / "adf_stationarity_comparison.csv"
    if adf_report_path.exists():
        adf_report_df = pd.read_csv(adf_report_path)
    else:
        adf_report_df = None

    for idx, col in enumerate(indicators):
        print(f"[{idx+1}/{len(indicators)}] Fitting and serializing models for {col}...")
        
        # 1. GET FULL SERIES FOR STATISTICAL MODELS
        train_y, test_y = prep.prepare_univariate_split('cleaned', col)
        full_y = pd.concat([train_y, test_y])
        
        # Fetch differencing order d from ADF stationarity report
        d_val = 1
        if adf_report_df is not None:
            match_row = adf_report_df[adf_report_df['Indicator'] == col]
            if not match_row.empty:
                d_str = str(match_row.iloc[0]['Cleaned_Required_d'])
                d_val = 0 if d_str == '0' else 1
        
        # Fit and save ARIMA
        try:
            arima_model = ARIMA(full_y, order=(1, d_val, 1))
            arima_fit = arima_model.fit()
            joblib.dump(arima_fit, subdirs['ARIMA'] / f"{col}_arima.joblib")
        except Exception as e:
            print(f"  ❌ ARIMA serialization failed: {e}")
            
        # Fit and save SARIMA
        try:
            sarima_model = SARIMAX(full_y, order=(1, d_val, 1), seasonal_order=(0, d_val, 0, 12))
            sarima_fit = sarima_model.fit(disp=False)
            joblib.dump(sarima_fit, subdirs['SARIMA'] / f"{col}_sarima.joblib")
        except Exception as e:
            print(f"  ❌ SARIMA serialization failed: {e}")
            
        # Fit and save Prophet
        try:
            df_prophet = pd.DataFrame({
                'ds': full_y.index.tz_localize(None),
                'y': full_y.values
            })
            prophet_model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            prophet_model.fit(df_prophet)
            joblib.dump(prophet_model, subdirs['Prophet'] / f"{col}_prophet.joblib")
        except Exception as e:
            print(f"  ❌ Prophet serialization failed: {e}")

        # 2. GET FULL DATA FOR MACHINE LEARNING REGRESSORS
        # Concatenate train and test sets to get full feature matrices
        X_train, X_test, y_train, y_test = prep.prepare_ml_features('cleaned', col)
        full_X = pd.concat([X_train, X_test])
        full_y_ml = pd.concat([y_train, y_test])
        
        # Fit and save Random Forest Regressor
        try:
            rf_reg = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
            rf_reg.fit(full_X, full_y_ml)
            joblib.dump(rf_reg, subdirs['RF'] / f"{col}_rf_reg.joblib")
        except Exception as e:
            print(f"  ❌ RF Regressor serialization failed: {e}")
            
        # Fit and save Gradient Boosting Regressor
        try:
            gb_reg = GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42)
            gb_reg.fit(full_X, full_y_ml)
            joblib.dump(gb_reg, subdirs['GB'] / f"{col}_gb_reg.joblib")
        except Exception as e:
            print(f"  ❌ GB Regressor serialization failed: {e}")

    print(f"\n✅ All production-ready models successfully serialized to: {models_dir}")

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4 - STEP 4.6: METRICS AGGREGATION & SERIALIZATION")
    print("=" * 60)
    
    # Paths
    tables_dir = project_root / "thesis" / "outputs" / "tables"
    models_dir = project_root / "thesis" / "outputs" / "models"
    os.makedirs(models_dir, exist_ok=True)
    
    raw_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Raw.csv"
    cleaned_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Cleaned.csv"
    
    prep = ImmunizationDataPrep(raw_csv, cleaned_csv)
    
    # 1. Compile Metrics
    compile_metrics(tables_dir)
    
    # 2. Serialize Production-Ready Models
    serialize_cleaned_models(prep, models_dir)
    
    print("\n✅ STEP 4.6 COMPLETE")
    print("=" * 60)
