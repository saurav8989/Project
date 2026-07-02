import os
import pandas as pd
import numpy as np
from scipy.stats import wilcoxon

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES_DIR = os.path.join(BASE_DIR, 'outputs', 'tables')

REG_SUMMARY_PATH = os.path.join(TABLES_DIR, 'regression_summary.csv')
CLS_SUMMARY_PATH = os.path.join(TABLES_DIR, 'classification_summary.csv')

REG_OUTPUT_PATH = os.path.join(TABLES_DIR, 'dqa_comparison_regression.csv')
CLS_OUTPUT_PATH = os.path.join(TABLES_DIR, 'dqa_comparison_classification.csv')

def run_regression_comparison():
    print("=" * 80)
    print("RUNNING REGRESSION METRICS COMPARISON (RAW VS CLEANED)")
    print("=" * 80)
    
    if not os.path.exists(REG_SUMMARY_PATH):
        print(f"Error: {REG_SUMMARY_PATH} does not exist.")
        return
        
    df = pd.read_csv(REG_SUMMARY_PATH)
    
    # 1. Parse and Align metrics (Step 5.1)
    df_raw = df[df['Dataset'] == 'Raw'].copy().sort_values('Indicator').reset_index(drop=True)
    df_cleaned = df[df['Dataset'] == 'Cleaned'].copy().sort_values('Indicator').reset_index(drop=True)
    
    # Verify indicator alignment
    if not df_raw['Indicator'].equals(df_cleaned['Indicator']):
        print("Warning: Indicators in Raw and Cleaned summaries do not align perfectly. Slicing common indicators.")
        common_indicators = set(df_raw['Indicator']).intersection(set(df_cleaned['Indicator']))
        df_raw = df_raw[df_raw['Indicator'].isin(common_indicators)].sort_values('Indicator').reset_index(drop=True)
        df_cleaned = df_cleaned[df_cleaned['Indicator'].isin(common_indicators)].sort_values('Indicator').reset_index(drop=True)
        
    indicators = df_raw['Indicator'].tolist()
    n_indicators = len(indicators)
    print(f"Aligned {n_indicators} indicators for paired analysis.")
    
    models = ['ARIMA', 'SARIMA', 'Prophet', 'RF', 'GB']
    metrics = ['RMSE', 'MAE']
    
    comparison_rows = []
    
    # 2. Run Wilcoxon Signed-Rank Test (Step 5.2)
    for model in models:
        for metric in metrics:
            col_name = f"{model}_{metric}"
            raw_vals = df_raw[col_name].values
            cleaned_vals = df_cleaned[col_name].values
            
            mean_raw = np.mean(raw_vals)
            mean_cleaned = np.mean(cleaned_vals)
            abs_reduction = mean_raw - mean_cleaned
            rel_reduction = (abs_reduction / mean_raw) * 100 if mean_raw != 0 else 0.0
            
            # Paired Wilcoxon Signed-Rank Test
            # Wilcoxon requires that differences are not all zero. If they are, p-value is 1.0.
            if np.allclose(raw_vals, cleaned_vals):
                stat = 0.0
                p_val = 1.0
            else:
                try:
                    stat, p_val = wilcoxon(raw_vals, cleaned_vals, alternative='two-sided')
                except Exception as e:
                    stat = 0.0
                    p_val = 1.0
                    
            significant = "Yes" if p_val < 0.05 else "No"
            
            comparison_rows.append({
                'Model': model,
                'Metric': metric,
                'Raw_Mean': mean_raw,
                'Cleaned_Mean': mean_cleaned,
                'Abs_Reduction': abs_reduction,
                'Rel_Reduction_Pct': rel_reduction,
                'Wilcoxon_Stat': stat,
                'P_Value': p_val,
                'Significant_p_0.05': significant
            })
            
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(REG_OUTPUT_PATH, index=False)
    print(f"Regression comparative results saved to {REG_OUTPUT_PATH}")
    
    # Format for display
    print("\nREGRESSION SUMMARY COMPARATIVE MATRIX:")
    print(comparison_df.to_markdown(index=False, floatfmt=".4f"))
    print("\n")

def run_classification_comparison():
    print("=" * 80)
    print("RUNNING CLASSIFICATION METRICS COMPARISON (RAW VS CLEANED)")
    print("=" * 80)
    
    if not os.path.exists(CLS_SUMMARY_PATH):
        print(f"Error: {CLS_SUMMARY_PATH} does not exist.")
        return
        
    df = pd.read_csv(CLS_SUMMARY_PATH)
    
    # 1. Parse and Align metrics (Step 5.1)
    df_raw = df[df['Dataset'] == 'Raw'].copy().sort_values(['Indicator', 'Risk_Type']).reset_index(drop=True)
    df_cleaned = df[df['Dataset'] == 'Cleaned'].copy().sort_values(['Indicator', 'Risk_Type']).reset_index(drop=True)
    
    # Align by merging on both keys
    merged = pd.merge(df_raw, df_cleaned, on=['Indicator', 'Risk_Type'], suffixes=('_raw', '_cleaned'))
    n_pairs = len(merged)
    print(f"Aligned {n_pairs} classification risk indicator pairs.")
    
    models = ['LR', 'RF', 'GB']
    metrics = ['Accuracy', 'Precision', 'Recall', 'F1', 'AUC']
    
    comparison_rows = []
    
    # 2. Run Wilcoxon Signed-Rank Test (Step 5.2)
    for model in models:
        for metric in metrics:
            raw_col = f"{model}_{metric}_raw"
            cleaned_col = f"{model}_{metric}_cleaned"
            
            raw_vals = merged[raw_col].fillna(0.0).values
            cleaned_vals = merged[cleaned_col].fillna(0.0).values
            
            mean_raw = np.mean(raw_vals)
            mean_cleaned = np.mean(cleaned_vals)
            abs_change = mean_cleaned - mean_raw  # Positive means improvement (higher F1/Recall)
            rel_change = (abs_change / mean_raw) * 100 if mean_raw != 0 else 0.0
            
            if np.allclose(raw_vals, cleaned_vals):
                stat = 0.0
                p_val = 1.0
            else:
                try:
                    stat, p_val = wilcoxon(raw_vals, cleaned_vals, alternative='two-sided')
                except Exception as e:
                    stat = 0.0
                    p_val = 1.0
                    
            significant = "Yes" if p_val < 0.05 else "No"
            
            comparison_rows.append({
                'Model': model,
                'Metric': metric,
                'Raw_Mean': mean_raw,
                'Cleaned_Mean': mean_cleaned,
                'Abs_Change': abs_change,
                'Rel_Change_Pct': rel_change,
                'Wilcoxon_Stat': stat,
                'P_Value': p_val,
                'Significant_p_0.05': significant
            })
            
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(CLS_OUTPUT_PATH, index=False)
    print(f"Classification comparative results saved to {CLS_OUTPUT_PATH}")
    
    # Format for display
    print("\nCLASSIFICATION SUMMARY COMPARATIVE MATRIX:")
    print(comparison_df.to_markdown(index=False, floatfmt=".4f"))
    print("\n")

if __name__ == '__main__':
    run_regression_comparison()
    run_classification_comparison()
