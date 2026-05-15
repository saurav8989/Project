import pandas as pd
from pathlib import Path
from load_data import load_dhis2_data

def inspect_and_save_report(df: pd.DataFrame, output_dir: Path):
    report_lines = []
    report_lines.append("=" * 50)
    report_lines.append("DATA INSPECTION & PROFILING REPORT")
    report_lines.append("=" * 50 + "\n")
    
    # 1. Shape
    report_lines.append("[1] SHAPE:")
    report_lines.append(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}\n")
    
    # 2. Columns
    report_lines.append("[2] COLUMNS:")
    report_lines.append(str(df.columns.tolist()) + "\n")
    
    # 3. Missing values summary
    report_lines.append("[3] MISSING VALUES SUMMARY:")
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if not missing_cols.empty:
        report_lines.append(missing_cols.to_string())
    else:
        report_lines.append("No missing values found!")
    report_lines.append("\n")
        
    # 4. Data types report
    report_lines.append("[4] DATA TYPES REPORT:")
    report_lines.append(df.dtypes.to_string() + "\n")
    
    # 5. Duplicate rows
    report_lines.append("[5] DUPLICATE ROWS:")
    duplicates = df.duplicated().sum()
    report_lines.append(f"Number of exact duplicate rows: {duplicates}\n")
    
    # 6. Vaccine indicator list
    report_lines.append("[6] VACCINE INDICATOR LIST:")
    vaccine_cols = [col for col in df.columns if "(Col " in col]
    report_lines.append(f"Identified {len(vaccine_cols)} vaccine columns:")
    for col in vaccine_cols:
        report_lines.append(f" - {col}")
        
    # Combine lines
    report_text = "\n".join(report_lines)
    
    # Print to console
    print(report_text)
    
    # Ensure outputs directory exists and save
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "profiling_report.txt"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print(f"\n✅ Profiling report successfully saved to: {report_path}")

if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    raw_data_path = project_root / "data" / "raw" / "Data.xlsx"
    outputs_dir = project_root / "outputs"
    
    if raw_data_path.exists():
        df = load_dhis2_data(str(raw_data_path))
        inspect_and_save_report(df, outputs_dir)
    else:
        print(f"❌ File not found at: {raw_data_path}")
