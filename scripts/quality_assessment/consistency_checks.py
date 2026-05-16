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

def assess_consistency(df, outputs_dir):
    print("=" * 50)
    print("B. INTERNAL CONSISTENCY CHECKS")
    print("=" * 50)
    
    # Define our Drop-out / Logical consistency rules
    # Tuple format: (Rule Name, Higher Expected Column, Lower Expected Column)
    rules = [
        ('Penta1 >= Penta2', 'Penta 1st (Col 13)', 'Penta 2nd (Col 14)'),
        ('Penta2 >= Penta3', 'Penta 2nd (Col 14)', 'Penta 3rd (Col 15)'),
        ('OPV1 >= OPV2', 'OPV 1st (Col 5)', 'OPV 2nd (Col 6)'),
        ('OPV2 >= OPV3', 'OPV 2nd (Col 6)', 'OPV 3rd (Col 7)'),
        ('PCV1 >= PCV2', 'PCV 1st (Col 10)', 'PCV 2nd (Col 11)'),
        ('PCV2 >= PCV3', 'PCV 2nd (Col 11)', 'PCV 3rd (Col 12)'),
        ('Rota1 >= Rota2', 'Rota 1st (Col 3)', 'Rota 2nd (Col 4)'),
        ('MR1 >= MR2', 'MR 1st (Col 16)', 'MR 2nd (Col 17)'),
        ('fIPV1 >= fIPV2', 'fIPV 1st (Col 8)', 'fIPV 2nd (Col 9)') # Added fIPV as bonus
    ]
    
    violations = []
    
    # Iterate through all rows to check for violations
    for idx, row in df.iterrows():
        for rule_name, col1, col2 in rules:
            val1 = row[col1]
            val2 = row[col2]
            
            # Check if both values exist and if the subsequent dose is greater than the prior dose
            if pd.notna(val1) and pd.notna(val2):
                if val2 > val1:
                    violations.append({
                        'SN': row['SN'],
                        'Fiscal Year': row['Fiscal Year'],
                        'Month (EN)': row['Month (EN)'],
                        'Month No.': row['Month No.'],
                        'District': row['District'],
                        'Rule': rule_name,
                        'Prior_Dose_Count': val1,
                        'Subsequent_Dose_Count': val2,
                        'Difference': val2 - val1
                    })
                    
    violations_df = pd.DataFrame(violations)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # ---------------------------------------------------------
    # 1. Violated Records
    # ---------------------------------------------------------
    print("\n[1] VIOLATED RECORDS:")
    if violations_df.empty:
        print("✅ No internal consistency violations found! (All Drop-out rules followed)")
    else:
        print(f"⚠️ Found {len(violations_df)} total rule violations across all records.")
        print("\nSample of violations:")
        # Drop 'Month No.' for display as it's just for sorting
        display_df = violations_df.drop(columns=['Month No.'])
        print(display_df.head(10).to_string(index=False))
        
        # Save full violations to CSV
        csv_path = outputs_dir / "consistency_violations.csv"
        display_df.to_csv(csv_path, index=False)
        print(f"\n📁 Full list of violated records saved to: {csv_path}")
        
        # ---------------------------------------------------------
        # 2. Violation Frequencies
        # ---------------------------------------------------------
        print("\n[2] VIOLATION FREQUENCIES (By Rule):")
        freq = violations_df['Rule'].value_counts().reset_index()
        freq.columns = ['Rule', 'Number of Violations']
        print(freq.to_string(index=False))
        
        # ---------------------------------------------------------
        # 3. Monthly Trend
        # ---------------------------------------------------------
        print("\n[3] MONTHLY TREND (Violations over time):")
        
        # Create an ordered list of months from the dataset
        month_order = df[['Month (EN)', 'Month No.']].drop_duplicates().sort_values('Month No.')['Month (EN)'].tolist()
        
        # Group by month and count
        monthly_counts = violations_df['Month (EN)'].value_counts().reindex(month_order).fillna(0).astype(int).reset_index()
        monthly_counts.columns = ['Month', 'Violations']
        print(monthly_counts.to_string(index=False))
        
        # Generate trend plot
        plt.figure(figsize=(10, 5))
        # Use hue mapping without a palette parameter when x and hue match to avoid warnings
        sns.barplot(data=monthly_counts, x='Month', y='Violations', color='salmon')
        plt.title('Data Consistency Violations by Month')
        plt.ylabel('Number of Violations')
        plt.xlabel('Month')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        trend_path = outputs_dir / "consistency_monthly_trend.png"
        plt.savefig(trend_path, dpi=300)
        print(f"\n📊 Monthly trend plot saved to: {trend_path}")

if __name__ == "__main__":
    raw_data_path = project_root / "data" / "raw" / "Data.xlsx"
    outputs_dir = project_root / "outputs"
    
    if raw_data_path.exists():
        df = load_dhis2_data(str(raw_data_path))
        assess_consistency(df, outputs_dir)
    else:
        print(f"❌ File not found at: {raw_data_path}")
