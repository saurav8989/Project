import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from scripts.data_loading.load_data import load_dhis2_data

def calculate_raw_indicators(df):
    """
    Step 2.1: Computes raw monthly coverage and dropout rates.
    Outliers (>100% coverage) and negative dropouts (logical violations) are left UNTOUCHED.
    """
    result_df = df[['SN', 'Fiscal Year', 'Month No.', 'Month (EN)', 'Month (NP)', 'District', 'Province', 'Surviving Infants (Monthly)']].copy()
    target_pop = df['Surviving Infants (Monthly)']
    
    # Vaccine column mapping
    vaccine_cols = {
        'BCG': 'BCG (Col 2)',
        'Rota_1': 'Rota 1st (Col 3)',
        'Rota_2': 'Rota 2nd (Col 4)',
        'OPV_1': 'OPV 1st (Col 5)',
        'OPV_2': 'OPV 2nd (Col 6)',
        'OPV_3': 'OPV 3rd (Col 7)',
        'fIPV_1': 'fIPV 1st (Col 8)',
        'fIPV_2': 'fIPV 2nd (Col 9)',
        'PCV_1': 'PCV 1st (Col 10)',
        'PCV_2': 'PCV 2nd (Col 11)',
        'PCV_3': 'PCV 3rd (Col 12)',
        'Penta_1': 'Penta 1st (Col 13)',
        'Penta_2': 'Penta 2nd (Col 14)',
        'Penta_3': 'Penta 3rd (Col 15)',
        'MR_1': 'MR 1st (Col 16)',
        'MR_2': 'MR 2nd (Col 17)',
        'JE': 'JE (Col 18)',
        'TCV': 'TCV (Col 19)'
    }
    
    # 1. Compute Doses and Coverage for each vaccine (un-capped)
    for key, col_name in vaccine_cols.items():
        doses = df[col_name].copy()
        
        # Calculate coverage (un-capped)
        with np.errstate(divide='ignore', invalid='ignore'):
            cov = np.where(target_pop > 0, (doses / target_pop) * 100, np.nan)
        
        result_df[f'{key}_Doses'] = doses
        result_df[f'{key}_Coverage'] = cov

    # 2. Compute Dropout Rates for multi-dose vaccines (allowing negative values)
    # Formula: ((Dose 1 - Dose n) / Dose 1) * 100
    dropout_definitions = {
        'Penta': ('Penta_1_Doses', 'Penta_3_Doses'),
        'OPV': ('OPV_1_Doses', 'OPV_3_Doses'),
        'PCV': ('PCV_1_Doses', 'PCV_3_Doses'),
        'Rota': ('Rota_1_Doses', 'Rota_2_Doses'),
        'MR': ('MR_1_Doses', 'MR_2_Doses'),
        'fIPV': ('fIPV_1_Doses', 'fIPV_2_Doses')
    }
    
    for family, (dose1_col, dosen_col) in dropout_definitions.items():
        d1 = result_df[dose1_col]
        dn = result_df[dosen_col]
        
        # Calculate dropout percentage (allowing negative values)
        # If Dose 1 is 0 or NaN, set dropout to NaN
        with np.errstate(divide='ignore', invalid='ignore'):
            dropout = np.where(d1 > 0, ((d1 - dn) / d1) * 100, np.nan)
            
        result_df[f'{family}_Dropout'] = dropout
        
    return result_df

def parse_fhir_bundle(bundle_path):
    """
    Step 2.2: Parses the master FHIR Bundle resource and extracts
    individual indicator records.
    """
    with open(bundle_path, 'r') as f:
        bundle = json.load(f)
        
    records = []
    
    # Mapping FHIR Measure IDs to standard Column Keys
    measure_mapping = {
        'measure-bcg': 'BCG',
        'measure-rota1': 'Rota_1',
        'measure-rota2': 'Rota_2',
        'measure-opv1': 'OPV_1',
        'measure-opv2': 'OPV_2',
        'measure-opv3': 'OPV_3',
        'measure-fipv1': 'fIPV_1',
        'measure-fipv2': 'fIPV_2',
        'measure-pcv1': 'PCV_1',
        'measure-pcv2': 'PCV_2',
        'measure-pcv3': 'PCV_3',
        'measure-penta1': 'Penta_1',
        'measure-penta2': 'Penta_2',
        'measure-penta3': 'Penta_3',
        'measure-mr1': 'MR_1',
        'measure-mr2': 'MR_2',
        'measure-je': 'JE',
        'measure-tcv': 'TCV'
    }
    
    entries = bundle.get('entry', [])
    print(f"Total Bundle entries found: {len(entries)}")
    
    for idx, entry in enumerate(entries):
        resource = entry.get('resource', {})
        if resource.get('resourceType') != 'MeasureReport':
            continue
            
        # Parse Measure ID
        measure_ref = resource.get('measure', '')
        measure_id = measure_ref.split('/')[-1]
        vaccine_key = measure_mapping.get(measure_id, measure_id)
        
        # Parse Extensions
        fiscal_year = None
        month_en = None
        month_np = None
        district = None
        
        fac_expected = None
        fac_reported = None
        fac_not_reported = None
        
        for ext in resource.get('extension', []):
            ext_url = ext.get('url')
            if ext_url == "http://example.org/fhir/StructureDefinition/nepali-fiscal-period":
                for sub in ext.get('extension', []):
                    if sub.get('url') == 'fiscalYear':
                        fiscal_year = sub.get('valueString')
                    elif sub.get('url') == 'monthEnglish':
                        month_en = sub.get('valueString')
                    elif sub.get('url') == 'monthNepali':
                        month_np = sub.get('valueString')
                    elif sub.get('url') == 'district':
                        district = sub.get('valueString')
            elif ext_url == "http://mohp.gov.np/fhir/StructureDefinition/facility-reporting-status":
                for sub in ext.get('extension', []):
                    if sub.get('url') == 'expected':
                        fac_expected = sub.get('valueInteger')
                    elif sub.get('url') == 'reported':
                        fac_reported = sub.get('valueInteger')
                    elif sub.get('url') == 'notReported':
                        fac_not_reported = sub.get('valueInteger')
                        
        # Parse Population counts
        denom_count = None
        num_count = None
        is_absent = False
        absent_reason = None
        
        for group in resource.get('group', []):
            for pop in group.get('population', []):
                pop_code = pop.get('code', {}).get('coding', [{}])[0].get('code')
                if pop_code == 'denominator':
                    denom_count = pop.get('count')
                elif pop_code == 'numerator':
                    num_count = pop.get('count')
                    # Check for data absent reason
                    for sub_ext in pop.get('extension', []):
                        if sub_ext.get('url') == "http://hl7.org/fhir/StructureDefinition/data-absent-reason":
                            is_absent = True
                            absent_reason = sub_ext.get('valueCode')
                            
        records.append({
            'Fiscal Year': fiscal_year,
            'Month (EN)': month_en,
            'Month (NP)': month_np,
            'District': district,
            'Vaccine_Key': vaccine_key,
            'Doses': num_count,
            'Is_Absent': is_absent,
            'Absent_Reason': absent_reason,
            'Surviving Infants (Monthly)': denom_count,
            'Facilities Expected': fac_expected,
            'Facilities Reported': fac_reported,
            'Facilities Not Reported': fac_not_reported
        })
        
    parsed_df = pd.DataFrame(records)
    return parsed_df

def assemble_pivoted_dataframe(parsed_df):
    """
    Step 2.3: Pivots the parsed long FHIR DataFrame (1080 rows) into a 
    wide DataFrame (60 rows) sorted chronologically by the Nepali Calendar.
    """
    # Pivot the long format to wide format, grouping by monthly identifiers
    pivot_cols = [
        'Fiscal Year', 'Month (EN)', 'Month (NP)', 'District',
        'Surviving Infants (Monthly)', 'Facilities Expected', 
        'Facilities Reported', 'Facilities Not Reported'
    ]
    
    df_pivot = parsed_df.pivot(
        index=pivot_cols,
        columns='Vaccine_Key',
        values='Doses'
    ).reset_index()
    
    # Map English month names to Nepali calendar month numbers (Shrawan = 1, Asar = 12)
    month_mapping = {
        'Shrawan': 1, 'Bhadra': 2, 'Ashwin': 3, 'Kartik': 4,
        'Mangsir': 5, 'Poush': 6, 'Magh': 7, 'Falgun': 8,
        'Chaitra': 9, 'Baishak': 10, 'Jestha': 11, 'Asar': 12
    }
    
    df_pivot['Month No.'] = df_pivot['Month (EN)'].map(month_mapping)
    
    # Sort chronologically by Fiscal Year and Month No.
    df_pivot = df_pivot.sort_values(by=['Fiscal Year', 'Month No.']).reset_index(drop=True)
    
    # Generate Serial Number (SN) from 1 to 60
    df_pivot.insert(0, 'SN', df_pivot.index + 1)
    
    # Reorder columns to place month details at the beginning
    desired_cols = [
        'SN', 'Fiscal Year', 'Month No.', 'Month (EN)', 'Month (NP)', 
        'District', 'Surviving Infants (Monthly)', 'Facilities Expected', 
        'Facilities Reported', 'Facilities Not Reported'
    ]
    
    vaccine_keys = [
        'BCG', 'Rota_1', 'Rota_2', 'OPV_1', 'OPV_2', 'OPV_3',
        'fIPV_1', 'fIPV_2', 'PCV_1', 'PCV_2', 'PCV_3', 
        'Penta_1', 'Penta_2', 'Penta_3', 'MR_1', 'MR_2', 'JE', 'TCV'
    ]
    
    df_pivot = df_pivot[desired_cols + vaccine_keys]
    return df_pivot

def calculate_cleaned_coverage(df_wide):
    """
    Step 2.4: Computes the monthly coverage rate for all 18 indicators
    on the pivoted FHIR DataFrame.
    """
    df = df_wide.copy()
    target_pop = df['Surviving Infants (Monthly)']
    
    vaccine_keys = [
        'BCG', 'Rota_1', 'Rota_2', 'OPV_1', 'OPV_2', 'OPV_3',
        'fIPV_1', 'fIPV_2', 'PCV_1', 'PCV_2', 'PCV_3', 
        'Penta_1', 'Penta_2', 'Penta_3', 'MR_1', 'MR_2', 'JE', 'TCV'
    ]
    
    for key in vaccine_keys:
        # Rename original count column to f'{key}_Doses'
        df = df.rename(columns={key: f'{key}_Doses'})
        doses = df[f'{key}_Doses'].copy()
        
        # Calculate coverage (un-capped for Step 2.4; capping will happen in Step 2.6)
        with np.errstate(divide='ignore', invalid='ignore'):
            cov = np.where(target_pop > 0, (doses / target_pop) * 100, 0.0)
            # Replace NaNs with 0.0 (e.g. for TCV when absent)
            cov = np.nan_to_num(cov, nan=0.0)
            
        df[f'{key}_Coverage'] = cov
        
    return df

if __name__ == "__main__":
    import json
    print("=" * 60)
    print("PHASE 2 - STEPS 2.1 to 2.4: INDICATOR EXTRACTION")
    print("=" * 60)
    
    # Define paths
    raw_data_path = project_root / "data" / "raw" / "Data.xlsx"
    fhir_bundle_path = project_root / "data" / "fhir" / "master_measurereports_bundle.json"
    thesis_output_dir = project_root / "thesis" / "outputs" / "tables"
    thesis_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 2.1: Process Raw Data
    if raw_data_path.exists():
        print(f"Loading raw dataset from: {raw_data_path}")
        raw_df = load_dhis2_data(str(raw_data_path))
        
        # Calculate Raw Indicators
        raw_indicators = calculate_raw_indicators(raw_df)
        
        # Save output
        raw_output_path = thesis_output_dir / "Indicators_Raw.csv"
        raw_indicators.to_csv(raw_output_path, index=False)
        print(f"✅ Successfully saved Raw Indicators to: {raw_output_path}")
        print(f"Shape: {raw_indicators.shape} (Rows: {raw_indicators.shape[0]}, Columns: {raw_indicators.shape[1]})")
    else:
        print(f"❌ Raw dataset not found at: {raw_data_path}")
        
    print("-" * 60)
    
    # Step 2.2 & 2.3: Load & Parse FHIR Bundle Data
    if fhir_bundle_path.exists():
        print(f"Loading master FHIR bundle from: {fhir_bundle_path}")
        fhir_parsed_df = parse_fhir_bundle(str(fhir_bundle_path))
        print("✅ FHIR Bundle successfully parsed!")
        
        # Step 2.3: Pivot and Assemble Wide DataFrame
        print("Assembling pivoted wide-format DataFrame...")
        fhir_wide_df = assemble_pivoted_dataframe(fhir_parsed_df)
        print("✅ FHIR DataFrame successfully pivoted!")
        
        # Step 2.4: Compute Cleaned Coverage
        print("Computing coverage rates on pivoted FHIR DataFrame...")
        fhir_cov_df = calculate_cleaned_coverage(fhir_wide_df)
        print("✅ Coverage rates successfully computed!")
        print(f"Shape after coverage: {fhir_cov_df.shape} (Rows: {fhir_cov_df.shape[0]}, Columns: {fhir_cov_df.shape[1]})")
        print("\nSample of computed coverage rates (showing doses and coverage side-by-side):")
        display_cols = [
            'SN', 'Fiscal Year', 'Month No.', 'Month (EN)', 
            'BCG_Doses', 'BCG_Coverage', 
            'Penta_1_Doses', 'Penta_1_Coverage'
        ]
        print(fhir_cov_df[display_cols].head(5).to_string(index=False))
    else:
        print(f"❌ FHIR bundle file not found at: {fhir_bundle_path}")
        
    print("\n✅ STEP 2.4 COMPLETE")
    print("=" * 60)
