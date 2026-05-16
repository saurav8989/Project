import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Add the project root to the path so we can import as a module
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from scripts.data_loading.load_data import load_dhis2_data

def detect_outliers(df, outputs_dir):
    print("=" * 50)
    print("C. COVERAGE & OUTLIER DETECTION")
    print("=" * 50)
    
    vaccine_cols = [col for col in df.columns if "(Col " in col]
    target_pop_col = 'Surviving Infants (Monthly)'
    
    # ---------------------------------------------------------
    # 1. Coverage Calculation (>100% Detection)
    # ---------------------------------------------------------
    # Formula: (Vaccinated Children / Target Population) * 100
    coverage_cols = []
    for col in vaccine_cols:
        cov_col = f"{col}_Coverage"
        coverage_cols.append(cov_col)
        # Avoid division by zero
        df[cov_col] = np.where(df[target_pop_col] > 0, 
                               (df[col] / df[target_pop_col]) * 100, 
                               np.nan)
        
    over_100 = []
    for cov_col in coverage_cols:
        vaccine_name = cov_col.replace('_Coverage', '')
        invalid = df[df[cov_col] > 100]
        for _, row in invalid.iterrows():
            over_100.append({
                'Fiscal Year': row['Fiscal Year'],
                'Month (EN)': row['Month (EN)'],
                'Vaccine': vaccine_name,
                'Doses': row[vaccine_name],
                'Target_Population': row[target_pop_col],
                'Coverage_Percent': row[cov_col]
            })
            
    over_100_df = pd.DataFrame(over_100)
    print(f"\n[1] >100% COVERAGE DETECTED: {len(over_100_df)} instances")
    if not over_100_df.empty:
        print(over_100_df[['Fiscal Year', 'Month (EN)', 'Vaccine', 'Coverage_Percent']].head().to_string(index=False))
        print("...")

    # ---------------------------------------------------------
    # 2. Z-Score & IQR Outlier Detection (Spikes & Drops)
    # ---------------------------------------------------------
    outliers = []
    
    for col in vaccine_cols:
        series = df[col].dropna()
        if len(series) < 5: continue
        
        # Z-score parameters
        mean = series.mean()
        std = series.std()
        
        # IQR parameters
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        for idx, val in series.items():
            z = (val - mean) / std if std > 0 else 0
            is_z_outlier = abs(z) > 3
            is_iqr_outlier = (val < lower_bound) or (val > upper_bound)
            
            if is_z_outlier or is_iqr_outlier:
                outlier_type = "Spike" if val > Q3 else "Drop"
                
                outliers.append({
                    'Fiscal Year': df.loc[idx, 'Fiscal Year'],
                    'Month (EN)': df.loc[idx, 'Month (EN)'],
                    'Vaccine': col,
                    'Value': val,
                    'Z-Score': round(z, 2),
                    'Lower Bound': lower_bound,
                    'Upper Bound': upper_bound,
                    'Type': outlier_type,
                    'Method': 'Both' if (is_z_outlier and is_iqr_outlier) else ('Z-Score' if is_z_outlier else 'IQR')
                })
                
    outliers_df = pd.DataFrame(outliers)
    print(f"\n[2] STATISTICAL OUTLIERS DETECTED (Spikes/Drops): {len(outliers_df)} instances")
    if not outliers_df.empty:
        print(outliers_df['Type'].value_counts().to_string())
        
    # ---------------------------------------------------------
    # 3. Save Outputs (Tables)
    # ---------------------------------------------------------
    outputs_dir.mkdir(parents=True, exist_ok=True)
    if not over_100_df.empty:
        over_100_df.to_csv(outputs_dir / "coverage_over_100.csv", index=False)
    if not outliers_df.empty:
        outliers_df.to_csv(outputs_dir / "statistical_outliers.csv", index=False)
    print(f"\n📁 Outlier CSV tables successfully saved to outputs/")

    # ---------------------------------------------------------
    # 4. Visualizations (Boxplots & Trends)
    # ---------------------------------------------------------
    
    # Visual 1: Boxplots
    plt.figure(figsize=(12, 10))
    sns.boxplot(data=df[vaccine_cols], orient='h', palette='viridis')
    plt.title('Vaccine Doses Distribution & Outliers (Boxplots)', pad=20, size=14)
    plt.xlabel('Number of Doses')
    plt.tight_layout()
    plt.savefig(outputs_dir / "outliers_boxplots.png", dpi=300)
    plt.close()
    
    # Visual 2: Trend Graph
    # Create a chronological axis
    df_sorted = df.sort_values(['Fiscal Year', 'Month No.']).copy()
    df_sorted['Time_Label'] = df_sorted['Fiscal Year'] + "-" + df_sorted['Month (EN)'].str[:3]
    
    x_labels = df_sorted['Time_Label'].tolist()
    x_pos = np.arange(len(x_labels))
    
    plt.figure(figsize=(15, 6))
    
    # Plot two main vaccines as examples
    plt.plot(x_pos, df_sorted['Penta 1st (Col 13)'], marker='o', label='Penta 1st', color='steelblue', alpha=0.8)
    plt.plot(x_pos, df_sorted['MR 1st (Col 16)'], marker='s', label='MR 1st', color='darkorange', alpha=0.8)
    
    # Highlight Outliers
    for _, row in outliers_df[outliers_df['Vaccine'] == 'Penta 1st (Col 13)'].iterrows():
        label = f"{row['Fiscal Year']}-{row['Month (EN)'][:3]}"
        if label in x_labels:
            plt.plot(x_labels.index(label), row['Value'], 'ro', markersize=12, fillstyle='none', markeredgewidth=2)
            
    for _, row in outliers_df[outliers_df['Vaccine'] == 'MR 1st (Col 16)'].iterrows():
        label = f"{row['Fiscal Year']}-{row['Month (EN)'][:3]}"
        if label in x_labels:
            plt.plot(x_labels.index(label), row['Value'], 'ro', markersize=12, fillstyle='none', markeredgewidth=2)
            
    plt.xticks(x_pos[::3], x_labels[::3], rotation=45, ha='right')
    plt.title('Vaccine Trend with Detected Outliers Circled in Red (Sudden Spikes/Drops)', pad=20, size=14)
    plt.ylabel('Number of Doses')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(outputs_dir / "outliers_trend.png", dpi=300)
    plt.close()
    
    print(f"📊 Boxplots and Trend graphs generated successfully!")

if __name__ == "__main__":
    raw_path = project_root / "data" / "raw" / "Data.xlsx"
    if raw_path.exists():
        df = load_dhis2_data(str(raw_path))
        detect_outliers(df, project_root / "outputs")
    else:
        print(f"❌ File not found at: {raw_path}")
