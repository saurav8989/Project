import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Add the project root to the path so we can import as a module
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from scripts.data_loading.load_data import load_dhis2_data

def assess_completeness(df, outputs_dir):
    print("=" * 50)
    print("A. COMPLETENESS ASSESSMENT")
    print("=" * 50)
    
    # Identify vaccine columns
    vaccine_cols = [col for col in df.columns if "(Col " in col]
    
    # ---------------------------------------------------------
    # 1. Reporting Completeness Calculation
    # ---------------------------------------------------------
    # Formula: (Facilities Reporting / 161) * 100
    df['Reporting_Completeness_Pct'] = (df['Facilities Reported'] / 161) * 100
    
    # ---------------------------------------------------------
    # 2. Year-wise Completeness
    # ---------------------------------------------------------
    year_completeness = df.groupby('Fiscal Year')['Reporting_Completeness_Pct'].mean().reset_index()
    print("\n--- Year-wise Reporting Completeness (%) ---")
    print(year_completeness.to_string(index=False))
    
    # ---------------------------------------------------------
    # 3. Monthly Completeness
    # ---------------------------------------------------------
    # Sort by Month No. to keep chronological order
    monthly_completeness = df.groupby(['Month No.', 'Month (EN)'])['Reporting_Completeness_Pct'].mean().reset_index()
    print("\n--- Monthly Reporting Completeness (%) ---")
    print(monthly_completeness[['Month (EN)', 'Reporting_Completeness_Pct']].to_string(index=False))
    
    # ---------------------------------------------------------
    # 4. Vaccine-wise Completeness (Indicator Completeness)
    # ---------------------------------------------------------
    # Formula: (Non-missing Values / Total Expected Values) * 100
    total_expected = len(df)
    vaccine_completeness = []
    
    for col in vaccine_cols:
        non_missing = df[col].notna().sum()
        completeness_pct = (non_missing / total_expected) * 100
        vaccine_completeness.append({'Vaccine': col, 'Indicator_Completeness_Pct': completeness_pct})
        
    vaccine_df = pd.DataFrame(vaccine_completeness)
    print("\n--- Vaccine-wise Indicator Completeness (%) ---")
    print(vaccine_df.to_string(index=False))
    
    # ---------------------------------------------------------
    # 5. Facility Completeness Heatmap
    # ---------------------------------------------------------
    # Create a pivot table: Rows = Fiscal Year, Columns = Month, Values = Reporting Completeness
    # We use 'Month No.' to sort correctly, then map to 'Month (EN)'
    pivot_df = df.pivot(index='Fiscal Year', columns='Month No.', values='Reporting_Completeness_Pct')
    
    # Rename columns to English months for the plot
    month_map = df[['Month No.', 'Month (EN)']].drop_duplicates().set_index('Month No.')['Month (EN)'].to_dict()
    pivot_df.rename(columns=month_map, inplace=True)
    
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap="YlGnBu", linewidths=.5, vmin=0, vmax=100)
    plt.title("Facility Reporting Completeness Heatmap (%) by Year and Month", pad=20)
    plt.ylabel("Fiscal Year")
    plt.xlabel("Month")
    plt.tight_layout()
    
    # Save the plot
    outputs_dir.mkdir(parents=True, exist_ok=True)
    heatmap_path = outputs_dir / "facility_completeness_heatmap.png"
    plt.savefig(heatmap_path, dpi=300)
    print(f"\n✅ Facility completeness heatmap saved to: {heatmap_path}")

if __name__ == "__main__":
    raw_data_path = project_root / "data" / "raw" / "Data.xlsx"
    outputs_dir = project_root / "outputs"
    
    if raw_data_path.exists():
        df = load_dhis2_data(str(raw_data_path))
        assess_completeness(df, outputs_dir)
    else:
        print(f"❌ File not found at: {raw_data_path}")
