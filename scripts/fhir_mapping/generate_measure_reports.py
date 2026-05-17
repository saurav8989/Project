import sys
import pandas as pd
from pathlib import Path

# Setup paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from fhir.resources.measurereport import MeasureReport, MeasureReportGroup, MeasureReportGroupPopulation
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.period import Period
from fhir.resources.quantity import Quantity
from fhir.resources.extension import Extension
from fhir.resources.bundle import Bundle, BundleEntry

def get_proxy_gregorian_dates(fiscal_year_str, month_no):
    """
    Approximates Gregorian dates from Nepali Fiscal Year.
    E.g., "2077/78" (BS) corresponds roughly to starting in mid-July 2020.
    This fulfills the FHIR requirement for standard charting, while 
    the FHIR extension preserves the exact native Nepali date.
    """
    try:
        bs_year = int(fiscal_year_str.split('/')[0])
        gregorian_start_year = bs_year - 57
    except:
        gregorian_start_year = 2020 # fallback
        
    # Rough mapping for Nepali months to Gregorian
    month_starts = {
        1: ("07-16", "08-15"), # Shrawan
        2: ("08-16", "09-15"), # Bhadra
        3: ("09-16", "10-16"), # Ashoj
        4: ("10-17", "11-15"), # Kartik
        5: ("11-16", "12-15"), # Mangsir
        6: ("12-16", "01-14"), # Poush
        7: ("01-15", "02-12"), # Magh
        8: ("02-13", "03-14"), # Falgun
        9: ("03-15", "04-13"), # Chaitra
        10: ("04-14", "05-14"), # Baishakh
        11: ("05-15", "06-14"), # Jestha
        12: ("06-15", "07-15")  # Ashad
    }
    
    start_md, end_md = month_starts.get(month_no, ("01-01", "01-31"))
    
    # Adjust for months crossing into the next Gregorian year
    s_year = gregorian_start_year if month_no < 6 else gregorian_start_year + 1
    e_year = gregorian_start_year if month_no < 5 else gregorian_start_year + 1
    
    # Special fix for end of Poush (month 6 crosses from Dec to Jan next year)
    if month_no == 6:
        s_year = gregorian_start_year
        e_year = gregorian_start_year + 1
        
    start_date = f"{s_year}-{start_md}T00:00:00Z"
    end_date = f"{e_year}-{end_md}T23:59:59Z"
    
    return start_date, end_date

def create_measure_report(row, measure_id, numerator_col):
    # Unique ID based on Measure and the row serial number (SN)
    report_id = f"{measure_id}-row-{row['SN']}"
    
    # 1. Custom Extension for precise Nepali Date ("Ground Truth")
    nepali_ext = Extension(
        url="http://example.org/fhir/StructureDefinition/nepali-fiscal-period",
        extension=[
            Extension(url="fiscalYear", valueString=str(row['Fiscal Year'])),
            Extension(url="monthEnglish", valueString=str(row['Month (EN)'])),
            Extension(url="monthNepali", valueString=str(row['Month (NP)'])),
            Extension(url="district", valueString=str(row['District']))
        ]
    )
    
    # 2. Rough Gregorian Period for standard FHIR dashboard plotting
    start_date, end_date = get_proxy_gregorian_dates(str(row['Fiscal Year']), int(row['Month No.']))
    period_obj = Period(start=start_date, end=end_date)
    
    report = MeasureReport(
        status="complete",
        type="summary",
        measure=f"http://example.org/fhir/Measure/{measure_id}",
        period=period_obj
    )
    report.id = report_id
    report.extension = [nepali_ext]
    
    # 3. Inject the Numerator and Denominator Data
    numerator_val = int(row[numerator_col])
    denominator_val = int(row['Surviving Infants (Monthly)'])
    
    # Handle DataAbsentReason if count is 0
    if numerator_val == 0:
        reason_code = "not-applicable" if "TCV" in numerator_col else "unknown"
        data_absent_ext = Extension(
            url="http://hl7.org/fhir/StructureDefinition/data-absent-reason",
            valueCode=reason_code
        )
        num_pop = MeasureReportGroupPopulation(
            code=CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/measure-population", code="numerator")]),
            extension=[data_absent_ext]
            # Notice we do NOT include the 'count' parameter here
        )
        score = 0.0
    else:
        num_pop = MeasureReportGroupPopulation(
            code=CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/measure-population", code="numerator")]),
            count=numerator_val
        )
        score = (numerator_val / denominator_val) * 100 if denominator_val > 0 else 0.0
    
    den_pop = MeasureReportGroupPopulation(
        code=CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/measure-population", code="denominator")]),
        count=denominator_val
    )
    
    ip_pop = MeasureReportGroupPopulation(
        code=CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/measure-population", code="initial-population")]),
        count=denominator_val
    )
    
    group = MeasureReportGroup(population=[ip_pop, den_pop, num_pop])
    
    # 4. Calculate Measure Score (Coverage Percentage)
    group.measureScoreQuantity = Quantity(value=round(score, 2), unit="%")
        
    report.group = [group]
    return report

def generate_reports():
    print("=" * 50)
    print("PHASE 6: FHIR MEASUREREPORT GENERATION")
    print("=" * 50)
    
    df_path = project_root / "data" / "processed" / "Cleaned_Data.csv"
    if not df_path.exists():
        print("❌ Error: Cleaned_Data.csv not found!")
        return
        
    df = pd.read_csv(df_path)
    
    indicators = [
        ("measure-bcg", "BCG (Col 2)"),
        ("measure-rota1", "Rota 1st (Col 3)"),
        ("measure-rota2", "Rota 2nd (Col 4)"),
        ("measure-opv1", "OPV 1st (Col 5)"),
        ("measure-opv2", "OPV 2nd (Col 6)"),
        ("measure-opv3", "OPV 3rd (Col 7)"),
        ("measure-fipv1", "fIPV 1st (Col 8)"),
        ("measure-fipv2", "fIPV 2nd (Col 9)"),
        ("measure-pcv1", "PCV 1st (Col 10)"),
        ("measure-pcv2", "PCV 2nd (Col 11)"),
        ("measure-pcv3", "PCV 3rd (Col 12)"),
        ("measure-penta1", "Penta 1st (Col 13)"),
        ("measure-penta2", "Penta 2nd (Col 14)"),
        ("measure-penta3", "Penta 3rd (Col 15)"),
        ("measure-mr1", "MR 1st (Col 16)"),
        ("measure-mr2", "MR 2nd (Col 17)"),
        ("measure-je", "JE (Col 18)"),
        ("measure-tcv", "TCV (Col 19)")
    ]
    
    # Initialize Master Bundle
    bundle = Bundle(type="collection")
    bundle.entry = []
    
    output_base_dir = project_root / "data" / "fhir" / "monthwise_measure_report"
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    count = 0
    # Iterate through all 60 rows of DHIS2 data
    for idx, row in df.iterrows():
        # Create a clean folder name for the month (e.g., "2077_78_01_Shrawan")
        fiscal_year_clean = str(row['Fiscal Year']).replace('/', '_')
        month_no_clean = str(row['Month No.']).zfill(2)
        month_en = str(row['Month (EN)'])
        folder_name = f"{fiscal_year_clean}_{month_no_clean}_{month_en}"
        
        month_dir = output_base_dir / folder_name
        month_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize a specific Bundle just for this month
        month_bundle = Bundle(type="collection")
        month_bundle.entry = []
        
        for measure_id, numerator_col in indicators:
            if numerator_col not in row:
                continue
                
            report = create_measure_report(row, measure_id, numerator_col)
            
            # Save individual report in the month's specific folder
            file_path = month_dir / f"{report.id}.json"
            with open(file_path, "w") as f:
                f.write(report.json(indent=2))
                
            # Add to both the Monthly Bundle and the Master Bundle
            entry = BundleEntry(fullUrl=f"http://example.org/fhir/MeasureReport/{report.id}", resource=report)
            month_bundle.entry.append(entry)
            bundle.entry.append(entry)
            count += 1
            
        # Save the Monthly Bundle
        month_bundle_path = month_dir / f"bundle_{folder_name}.json"
        with open(month_bundle_path, "w") as f:
            f.write(month_bundle.json(indent=2))
            
    # Save the master Bundle
    bundle_path = project_root / "data" / "fhir" / "master_measurereports_bundle.json"
    with open(bundle_path, "w") as f:
        f.write(bundle.json(indent=2))
            
    print(f"✅ Generated {count} individual FHIR MeasureReport resources!")
    print(f"✅ Organized all files into 60 month-wise directories inside: {output_base_dir.name}/")
    print(f"✅ Created a Master FHIR Bundle containing ALL reports at: {bundle_path.name}")

if __name__ == "__main__":
    generate_reports()
