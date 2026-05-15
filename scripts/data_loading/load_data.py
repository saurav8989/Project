import pandas as pd
from pathlib import Path

def load_dhis2_data(file_path: str) -> pd.DataFrame:
    """
    Loads DHIS2 Excel data, skipping the initial title rows.
    
    Args:
        file_path (str): Path to the raw Excel file.
        
    Returns:
        pd.DataFrame: The loaded DataFrame with original headers.
    """
    # Load data using the 3rd row (index 2) as header
    df = pd.read_excel(file_path, sheet_name='District Monthly Data', header=2)
    
    # Clean spacing issues in column names without removing actual text
    clean_cols = []
    for col in df.columns:
        if isinstance(col, str):
            # Replace newlines with a space
            c = col.replace('\n', ' ')
            # Remove duplicate spaces and strip leading/trailing spaces
            c = " ".join(c.split())
            clean_cols.append(c)
        else:
            clean_cols.append(col)
            
    df.columns = clean_cols
    return df

if __name__ == "__main__":
    # Define paths relative to this script
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    raw_data_path = project_root / "data" / "raw" / "Data.xlsx"
    
    print(f"Looking for data at: {raw_data_path}")
    
    if raw_data_path.exists():
        df = load_dhis2_data(str(raw_data_path))
        print("\n✅ Data loaded successfully!")
        print(f"Shape: {df.shape} (Rows: {df.shape[0]}, Columns: {df.shape[1]})")
        
        print("\n--- Original Columns ---")
        for i, col in enumerate(df.columns):
            print(f"{i}: {col}")
            
        print("\n--- First 2 rows of data ---")
        print(df.head(2).to_string())
    else:
        print(f"❌ File not found at: {raw_data_path}")
