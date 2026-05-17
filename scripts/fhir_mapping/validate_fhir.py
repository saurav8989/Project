import sys
from pathlib import Path
import json

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from fhir.resources.measure import Measure
from fhir.resources.measurereport import MeasureReport

def validate_fhir_resources():
    print("=" * 50)
    print("PHASE 6: FHIR VALIDATION")
    print("=" * 50)
    
    fhir_data_dir = project_root / "data" / "fhir"
    
    report_lines = []
    report_lines.append("==================================================")
    report_lines.append("FHIR VALIDATION REPORT")
    report_lines.append("==================================================\n")
    
    # ---------------------------------------------------------
    # 1. Validate Measures
    # ---------------------------------------------------------
    measure_dir = fhir_data_dir / "measures"
    measure_files = list(measure_dir.glob("*.json"))
    
    report_lines.append("1. MEASURE BLUEPRINT VALIDATION")
    report_lines.append("-" * 50)
    
    measures_passed = 0
    for m_file in measure_files:
        try:
            # Pydantic parsing enforces strict FHIR structure and types
            Measure.parse_file(m_file)
            measures_passed += 1
        except Exception as e:
            report_lines.append(f"❌ Structural Error in {m_file.name}: {str(e)}")
            
    report_lines.append(f"Total Measure Resources Audited: {len(measure_files)}")
    report_lines.append(f"Structurally Valid: {measures_passed}/{len(measure_files)}")
    report_lines.append("Status: " + ("PASS" if measures_passed == len(measure_files) else "FAIL"))
    report_lines.append("\n")
    
    # ---------------------------------------------------------
    # 2. Validate MeasureReports
    # ---------------------------------------------------------
    mr_base_dir = fhir_data_dir / "monthwise_measure_report"
    # Find all JSON files except the bundle aggregations
    mr_files = list(mr_base_dir.rglob("measure-*.json"))
    
    report_lines.append("2. MEASUREREPORT DATA VALIDATION")
    report_lines.append("-" * 50)
    
    mr_passed_structure = 0
    mr_passed_logic = 0
    logic_errors = []
    
    for mr_file in mr_files:
        try:
            # A. Structural Validation (FHIR R4 Schema compliance)
            mr = MeasureReport.parse_file(mr_file)
            mr_passed_structure += 1
            
            # B. Logical Consistency Validation
            if mr.group and len(mr.group) > 0:
                group = mr.group[0]
                num_count = 0
                den_count = 0
                
                # Check Populations
                for pop in group.population:
                    pop_code = pop.code.coding[0].code
                    if pop_code == "numerator":
                        if pop.count is not None:
                            num_count = pop.count
                        else:
                            # If count is missing, ensure DataAbsentReason exists
                            has_dar = False
                            if pop.extension:
                                for ext in pop.extension:
                                    if ext.url == "http://hl7.org/fhir/StructureDefinition/data-absent-reason":
                                        has_dar = True
                                        break
                            if not has_dar:
                                logic_errors.append(f"{mr.id}: Missing count AND missing DataAbsentReason.")
                                
                    elif pop_code == "denominator":
                        if pop.count is not None:
                            den_count = pop.count
                            
                # Check Mathematical Consistency
                expected_score = 0.0
                if den_count > 0:
                    expected_score = round((num_count / den_count) * 100, 2)
                    
                actual_score = float(group.measureScoreQuantity.value) if group.measureScoreQuantity else 0.0
                
                # Using a small epsilon for floating point comparison
                if abs(expected_score - actual_score) > 0.01:
                    logic_errors.append(f"{mr.id}: Math Mismatch. Numerator={num_count}, Denominator={den_count}, Expected={expected_score}%, Actual={actual_score}%")
                else:
                    mr_passed_logic += 1
                    
        except Exception as e:
            report_lines.append(f"❌ Structural Error in {mr_file.name}: {str(e)}")
            
    report_lines.append(f"Total MeasureReport Resources Audited: {len(mr_files)}")
    report_lines.append(f"Structurally Valid (FHIR R4 Schema): {mr_passed_structure}/{len(mr_files)}")
    report_lines.append(f"Logically Consistent (Math & Extensions): {mr_passed_logic}/{mr_passed_structure}")
    
    if logic_errors:
        report_lines.append("\nLogical Errors Detected:")
        for err in logic_errors[:10]: # Print first 10
            report_lines.append(f"- {err}")
        if len(logic_errors) > 10:
            report_lines.append(f"... and {len(logic_errors) - 10} more.")
            
    status = "PASS" if (mr_passed_structure == len(mr_files) and mr_passed_logic == mr_passed_structure) else "FAIL"
    report_lines.append(f"Status: {status}\n")
    
    # ---------------------------------------------------------
    # Output the Report
    # ---------------------------------------------------------
    out_path = project_root / "outputs" / "fhir_validation_report.txt"
    out_path.write_text("\n".join(report_lines))
    
    print("\n".join(report_lines))
    print(f"\n✅ Detailed validation report saved to: {out_path.relative_to(project_root)}")

if __name__ == "__main__":
    validate_fhir_resources()
