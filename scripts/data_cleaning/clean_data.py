import sys
import pandas as pd
from pathlib import Path

# Setup paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from scripts.data_loading.load_data import load_dhis2_data

def clean_data(df, outputs_dir):
    print("=" * 50)
    print("PHASE 5: DATA CLEANING PIPELINE")
    print("=" * 50)
    
    # Create a copy so we don't modify the loaded one directly if used in memory
    cleaned_df = df.copy()
    
    print("1. Handling Missing Reporting Data...")
    print("   -> Missing 'Facilities Reported' filled with 0")
    print("   -> Missing 'Facilities Not Reported' filled with 161")
    # If Facilities Reported is missing, we assume 0 facilities reported.
    cleaned_df['Facilities Reported'] = cleaned_df['Facilities Reported'].fillna(0)
    
    # If 0 reported, then all 161 expected facilities failed to report.
    cleaned_df['Facilities Not Reported'] = cleaned_df['Facilities Not Reported'].fillna(161)
    
    print("2. Handling Missing TCV Data...")
    print("   -> All NaN values in TCV replaced with 0 (Clinically accurate for pre-introduction dates)")
    # Dynamically find the TCV column (it is 'TCV (Col 19)' in the dataset)
    tcv_cols = [col for col in cleaned_df.columns if 'TCV' in col]
    for col in tcv_cols:
        cleaned_df[col] = cleaned_df[col].fillna(0)
        
    print("3. Standardizing Data Types...")
    print("   -> All float64 columns dynamically converted to int64 (No partial vaccines allowed)")
    # Now that there are no NaNs, we can safely convert all numeric columns from float64 to int64
    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == 'float64':
            cleaned_df[col] = cleaned_df[col].astype('int64')

    print("4. Handling Outliers & Drop-out Logic...")
    print("   -> Outliers (>100% Coverage) left UNTOUCHED for FHIR MeasureReport aggregation.")
    print("   -> Drop-out logic violations left UNTOUCHED to preserve raw aggregate counts.")
            
    print("\n✅ DATA CLEANING COMPLETE")
    
    # Save the cleaned dataset
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / "Cleaned_Data.csv"
    cleaned_df.to_csv(output_file, index=False)
    
    print(f"\n📁 Cleaned dataset successfully saved to: {output_file}")
    
    return cleaned_df

if __name__ == "__main__":
    raw_path = project_root / "data" / "raw" / "Data.xlsx"
    if raw_path.exists():
        df = load_dhis2_data(str(raw_path))
        clean_data(df, project_root / "outputs")
    else:
        print(f"❌ File not found at: {raw_path}")
