import sys
import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaErrors
from pathlib import Path

# Add the project root to the path so we can import as a module
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from scripts.data_loading.load_data import load_dhis2_data

def validate_dhis2_schema(df, outputs_dir):
    print("=" * 50)
    print("PHASE 4: AUTOMATED RULE-BASED VALIDATION (PANDERA)")
    print("=" * 50)
    
    # 1. DEFINE THE STRICT SCHEMA
    # We set nullable=True for numeric columns to ensure we don't drop rows with NaNs (like TCV)
    schema_dict = {
        "Fiscal Year": pa.Column(pa.String, nullable=False),
        "Month No.": pa.Column(pa.Int, nullable=False, checks=[pa.Check.ge(1), pa.Check.le(12)]),
        "Month (EN)": pa.Column(pa.String, nullable=False),
        "District": pa.Column(pa.String, nullable=False),
        "Surviving Infants (Monthly)": pa.Column(pa.Int, nullable=False, checks=pa.Check.ge(0)),
        "Facilities Reported": pa.Column(float, nullable=True),
        "Facilities Not Reported": pa.Column(float, nullable=True),
    }
    
    # Dynamically add all vaccine columns to ensure they are at least >= 0
    vaccine_cols = [col for col in df.columns if "(Col " in col]
    for col in vaccine_cols:
        schema_dict[col] = pa.Column(float, nullable=True, checks=pa.Check.ge(0))
        
    # 2. DEFINE THE DATA FRAME SCHEMA WITH DROP-OUT RULES
    schema = pa.DataFrameSchema(
        schema_dict,
        strict=False, # strict=False ensures we DO NOT drop any extra columns in the DataFrame
        checks=[
            # Logical Consistency Rules (Dose 1 >= Dose 2 >= Dose 3)
            pa.Check(lambda df: df["Penta 1st (Col 13)"] >= df["Penta 2nd (Col 14)"], name="Penta1 >= Penta2", ignore_na=True),
            pa.Check(lambda df: df["Penta 2nd (Col 14)"] >= df["Penta 3rd (Col 15)"], name="Penta2 >= Penta3", ignore_na=True),
            pa.Check(lambda df: df["OPV 1st (Col 7)"] >= df["OPV 2nd (Col 8)"], name="OPV1 >= OPV2", ignore_na=True),
            pa.Check(lambda df: df["OPV 2nd (Col 8)"] >= df["OPV 3rd (Col 9)"], name="OPV2 >= OPV3", ignore_na=True),
            pa.Check(lambda df: df["PCV 1st (Col 10)"] >= df["PCV 2nd (Col 11)"], name="PCV1 >= PCV2", ignore_na=True),
            pa.Check(lambda df: df["PCV 2nd (Col 11)"] >= df["PCV 3rd (Col 12)"], name="PCV2 >= PCV3", ignore_na=True),
            pa.Check(lambda df: df["MR 1st (Col 16)"] >= df["MR 2nd (Col 17)"], name="MR1 >= MR2", ignore_na=True),
            pa.Check(lambda df: df["Rota 1st (Col 5)"] >= df["Rota 2nd (Col 6)"], name="Rota1 >= Rota2", ignore_na=True),
            pa.Check(lambda df: df["fIPV 1st (Col 20)"] >= df["fIPV 2nd (Col 21)"], name="fIPV1 >= fIPV2", ignore_na=True),
        ]
    )
    
    print("RULES ENFORCED IN THIS SCHEMA:")
    print("1. DATA TYPES: Month No. (1-12), Surviving Infants (>=0), All Vaccines (>=0)")
    print("2. DROP-OUT LOGIC:")
    print("   - Penta 1st >= Penta 2nd >= Penta 3rd")
    print("   - OPV 1st >= OPV 2nd >= OPV 3rd")
    print("   - PCV 1st >= PCV 2nd >= PCV 3rd")
    print("   - MR 1st >= MR 2nd")
    print("   - Rota 1st >= Rota 2nd")
    print("   - fIPV 1st >= fIPV 2nd")
    print("-" * 50)
    
    print(f"Scanning {len(df)} records without modifying original data...")
    
    # 3. RUN LAZY VALIDATION
    try:
        # lazy=True ensures it scans ALL rows and collects all errors, instead of stopping at the first error.
        validated_df = schema.validate(df, lazy=True)
        print("✅ SUCCESS: Data passed all validation rules!")
        return validated_df
        
    except SchemaErrors as err:
        print(f"❌ VALIDATION FAILED: Found {len(err.failure_cases)} data quality violations.")
        
        # Save the log of errors for thesis documentation
        failures_df = err.failure_cases
        outputs_dir.mkdir(parents=True, exist_ok=True)
        failures_df.to_csv(outputs_dir / "pandera_validation_errors.csv", index=False)
        print(f"📁 Detailed validation log saved to: {outputs_dir}/pandera_validation_errors.csv")
        
        print("\nSummary of Failed Rules:")
        print(failures_df['check'].value_counts().to_string())
        
        print("\n🛡️  ACTION TAKEN: None. The script is bypassing the errors and returning the 100% original DataFrame for FHIR mapping.")
        return df # We return the raw, unmodified dataframe so absolutely NO DATA IS REMOVED

if __name__ == "__main__":
    df = load_dhis2_data(str(project_root / "data" / "raw" / "Data.xlsx"))
    validate_dhis2_schema(df, project_root / "outputs")
