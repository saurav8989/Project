import os
import pandas as pd
import numpy as np
import joblib

TABLES_DIR = "thesis/outputs/tables"
MODELS_DIR = "thesis/outputs/models"

def generate_hybrid_predictions(suffix="cleaned"):
    # File paths
    metrics_arima_file = os.path.join(TABLES_DIR, f"metrics_arima_sarima_{suffix}.csv")
    metrics_prophet_file = os.path.join(TABLES_DIR, f"metrics_prophet_{suffix}.csv")
    metrics_ml_file = os.path.join(TABLES_DIR, f"metrics_ml_{suffix}.csv")
    
    pred_arima_file = os.path.join(TABLES_DIR, f"predictions_arima_sarima_{suffix}.csv")
    pred_prophet_file = os.path.join(TABLES_DIR, f"predictions_prophet_{suffix}.csv")
    pred_ml_file = os.path.join(TABLES_DIR, f"predictions_ml_{suffix}.csv")
    
    # Check existence
    files_exist = [
        os.path.exists(metrics_arima_file),
        os.path.exists(metrics_prophet_file),
        os.path.exists(metrics_ml_file),
        os.path.exists(pred_arima_file),
        os.path.exists(pred_prophet_file),
        os.path.exists(pred_ml_file)
    ]
    
    if not all(files_exist):
        print(f"Error: Missing baseline prediction/metric files for suffix: {suffix}")
        return
        
    # Read files
    df_m_arima = pd.read_csv(metrics_arima_file)
    df_m_prophet = pd.read_csv(metrics_prophet_file)
    df_m_ml = pd.read_csv(metrics_ml_file)
    
    df_p_arima = pd.read_csv(pred_arima_file)
    df_p_prophet = pd.read_csv(pred_prophet_file)
    df_p_ml = pd.read_csv(pred_ml_file)
    
    indicators = df_p_arima['Indicator'].unique()
    
    all_predictions = []
    all_metrics = []
    weights_serialized = {}
    
    for ind in indicators:
        # Extract MAEs
        mae_arima = df_m_arima.loc[df_m_arima['Indicator'] == ind, 'ARIMA_MAE'].values
        mae_sarima = df_m_arima.loc[df_m_arima['Indicator'] == ind, 'SARIMA_MAE'].values
        mae_prophet = df_m_prophet.loc[df_m_prophet['Indicator'] == ind, 'Prophet_MAE'].values
        mae_rf = df_m_ml.loc[df_m_ml['Indicator'] == ind, 'RF_MAE'].values
        mae_gb = df_m_ml.loc[df_m_ml['Indicator'] == ind, 'GB_MAE'].values
        
        if len(mae_arima) == 0 or len(mae_sarima) == 0 or len(mae_prophet) == 0 or len(mae_rf) == 0 or len(mae_gb) == 0:
            print(f"Warning: Missing metric values for indicator {ind} ({suffix})")
            continue
            
        mae_arima = mae_arima[0]
        mae_sarima = mae_sarima[0]
        mae_prophet = mae_prophet[0]
        mae_rf = mae_rf[0]
        mae_gb = mae_gb[0]
        
        # Avoid division by zero
        mae_arima = max(1e-5, mae_arima)
        mae_sarima = max(1e-5, mae_sarima)
        mae_prophet = max(1e-5, mae_prophet)
        mae_rf = max(1e-5, mae_rf)
        mae_gb = max(1e-5, mae_gb)
        
        # Calculate weights (inverse MAE)
        inv_arima = 1.0 / mae_arima
        inv_sarima = 1.0 / mae_sarima
        inv_prophet = 1.0 / mae_prophet
        inv_rf = 1.0 / mae_rf
        inv_gb = 1.0 / mae_gb
        
        total_inv = inv_arima + inv_sarima + inv_prophet + inv_rf + inv_gb
        
        w_arima = inv_arima / total_inv
        w_sarima = inv_sarima / total_inv
        w_prophet = inv_prophet / total_inv
        w_rf = inv_rf / total_inv
        w_gb = inv_gb / total_inv
        
        weights_serialized[ind] = {
            'ARIMA': w_arima,
            'SARIMA': w_sarima,
            'Prophet': w_prophet,
            'RF': w_rf,
            'GB': w_gb
        }
        
        # Filter forecasts
        p_arima = df_p_arima[df_p_arima['Indicator'] == ind].sort_values('Month No.').reset_index(drop=True)
        p_prophet = df_p_prophet[df_p_prophet['Indicator'] == ind].sort_values('Month No.').reset_index(drop=True)
        p_ml = df_p_ml[df_p_ml['Indicator'] == ind].sort_values('Month No.').reset_index(drop=True)
        
        if len(p_arima) != 12 or len(p_prophet) != 12 or len(p_ml) != 12:
            print(f"Warning: Row count mismatch for indicator {ind} ({suffix})")
            continue
            
        # Compute Hybrid Forecast
        hybrid_fc = (
            w_arima * p_arima['ARIMA_Forecast'] +
            w_sarima * p_arima['SARIMA_Forecast'] +
            w_prophet * p_prophet['Prophet_Forecast'] +
            w_rf * p_ml['RF_Forecast'] +
            w_gb * p_ml['GB_Forecast']
        )
        
        # Build predictions DataFrame
        p_hybrid = p_arima[['Indicator', 'Fiscal Year', 'Month No.', 'Month (EN)', 'Month (NP)', 'Actual']].copy()
        p_hybrid['Hybrid_Forecast'] = hybrid_fc
        all_predictions.append(p_hybrid)
        
        # Calculate metrics
        actuals = p_hybrid['Actual'].values
        preds = p_hybrid['Hybrid_Forecast'].values
        
        mask = ~np.isnan(actuals)
        if mask.sum() > 0:
            mae = np.mean(np.abs(actuals[mask] - preds[mask]))
            rmse = np.sqrt(np.mean((actuals[mask] - preds[mask]) ** 2))
            actuals_mape = actuals[mask]
            preds_mape = preds[mask]
            mape_mask = actuals_mape != 0
            if mape_mask.sum() > 0:
                mape = np.mean(np.abs((actuals_mape[mape_mask] - preds_mape[mape_mask]) / actuals_mape[mape_mask])) * 100.0
            else:
                mape = 0.0
        else:
            mae, rmse, mape = 0.0, 0.0, 0.0
            
        all_metrics.append({
            'Indicator': ind,
            'Hybrid_MAE': mae,
            'Hybrid_RMSE': rmse,
            'Hybrid_MAPE': mape,
            'Weight_ARIMA': w_arima,
            'Weight_SARIMA': w_sarima,
            'Weight_Prophet': w_prophet,
            'Weight_RF': w_rf,
            'Weight_GB': w_gb
        })
        
    if len(all_predictions) > 0:
        pd.concat(all_predictions, ignore_index=True).to_csv(os.path.join(TABLES_DIR, f"predictions_hybrid_{suffix}.csv"), index=False)
        pd.DataFrame(all_metrics).to_csv(os.path.join(TABLES_DIR, f"metrics_hybrid_{suffix}.csv"), index=False)
        print(f"Generated hybrid predictions and metrics for suffix: {suffix}")
        
        # Generate and save weight distribution table (Phase 4.6 style for report copy-paste)
        weights_df = pd.DataFrame([
            {
                'Indicator': m['Indicator'],
                'ARIMA Weight (%)': round(m['Weight_ARIMA'] * 100, 2),
                'SARIMA Weight (%)': round(m['Weight_SARIMA'] * 100, 2),
                'Prophet Weight (%)': round(m['Weight_Prophet'] * 100, 2),
                'RF Weight (%)': round(m['Weight_RF'] * 100, 2),
                'GB Weight (%)': round(m['Weight_GB'] * 100, 2),
                'Total (%)': round((m['Weight_ARIMA'] + m['Weight_SARIMA'] + m['Weight_Prophet'] + m['Weight_RF'] + m['Weight_GB']) * 100, 2)
            } for m in all_metrics
        ])
        weights_csv_path = os.path.join(TABLES_DIR, f"hybrid_weights_distribution_{suffix}.csv")
        weights_df.to_csv(weights_csv_path, index=False)
        print(f"Generated weight distribution CSV: {weights_csv_path}")
        
        # Serialize the weights (Phase 4.6 Style)
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib_path = os.path.join(MODELS_DIR, f"hybrid_weights_{suffix}.joblib")
        joblib.dump(weights_serialized, joblib_path)
        print(f"Serialized hybrid weights to: {joblib_path}")

if __name__ == "__main__":
    print("Running Performance-Weighted Hybrid Ensemble generation...")
    generate_hybrid_predictions("cleaned")
    generate_hybrid_predictions("raw")
    print("Hybrid Ensemble generation complete!")
