import sys
import json
from pathlib import Path

# Add the project root to the path so we can import as a module
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from fhir.resources.measure import Measure, MeasureGroup, MeasureGroupPopulation
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.expression import Expression
from fhir.resources.bundle import Bundle, BundleEntry

def create_measure(vaccine_name, measure_id, numerator_desc, denominator_desc):
    # FHIR Measure Resource instantiation
    measure = Measure(
        status="active", 
        name=measure_id.replace('-', '_')
    )
    measure.id = measure_id
    measure.url = f"http://example.org/fhir/Measure/{measure_id}"
    measure.title = f"{vaccine_name} Coverage Measure"
    measure.description = f"DHIS2 Aggregate Indicator defining the monthly coverage of the {vaccine_name} vaccine."
    
    # 1. Define Numerator (The Dose Count)
    num_population = MeasureGroupPopulation(
        code=CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/measure-population", code="numerator")]),
        description=f"Numerator: {numerator_desc}",
        criteria=Expression(language="text/cql", expression="Count of Doses Administered")
    )
    
    # 2. Define Denominator (The Target Population)
    den_population = MeasureGroupPopulation(
        code=CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/measure-population", code="denominator")]),
        description=f"Denominator: {denominator_desc}",
        criteria=Expression(language="text/cql", expression="Count of Surviving Infants")
    )
    
    # 3. Define Initial Population (Often the same as Denominator in public health)
    ip_population = MeasureGroupPopulation(
        code=CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/measure-population", code="initial-population")]),
        description=f"Initial Population: {denominator_desc}",
        criteria=Expression(language="text/cql", expression="Count of Surviving Infants")
    )
    
    # Attach the populations to the Measure Group
    measure.group = [MeasureGroup(population=[ip_population, den_population, num_population])]
    
    return measure

def generate_all_measures():
    print("=" * 50)
    print("PHASE 6: FHIR MEASURE GENERATION")
    print("=" * 50)
    
    # The Mapping Table from Step B
    indicators = [
        ("BCG", "measure-bcg", "BCG (Col 2)"),
        ("Rota 1st", "measure-rota1", "Rota 1st (Col 3)"),
        ("Rota 2nd", "measure-rota2", "Rota 2nd (Col 4)"),
        ("OPV 1st", "measure-opv1", "OPV 1st (Col 5)"),
        ("OPV 2nd", "measure-opv2", "OPV 2nd (Col 6)"),
        ("OPV 3rd", "measure-opv3", "OPV 3rd (Col 7)"),
        ("fIPV 1st", "measure-fipv1", "fIPV 1st (Col 8)"),
        ("fIPV 2nd", "measure-fipv2", "fIPV 2nd (Col 9)"),
        ("PCV 1st", "measure-pcv1", "PCV 1st (Col 10)"),
        ("PCV 2nd", "measure-pcv2", "PCV 2nd (Col 11)"),
        ("PCV 3rd", "measure-pcv3", "PCV 3rd (Col 12)"),
        ("Penta 1st", "measure-penta1", "Penta 1st (Col 13)"),
        ("Penta 2nd", "measure-penta2", "Penta 2nd (Col 14)"),
        ("Penta 3rd", "measure-penta3", "Penta 3rd (Col 15)"),
        ("MR 1st", "measure-mr1", "MR 1st (Col 16)"),
        ("MR 2nd", "measure-mr2", "MR 2nd (Col 17)"),
        ("JE", "measure-je", "JE (Col 18)"),
        ("TCV", "measure-tcv", "TCV (Col 19)")
    ]
    
    output_dir = project_root / "data" / "fhir" / "measures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize a FHIR Bundle (type 'collection')
    bundle = Bundle(type="collection")
    bundle.entry = []
    
    for vaccine_name, measure_id, numerator_col in indicators:
        measure = create_measure(
            vaccine_name=vaccine_name,
            measure_id=measure_id,
            numerator_desc=numerator_col,
            denominator_desc="Surviving Infants (Monthly)"
        )
        
        # Save individual Measure as standard FHIR JSON
        file_path = output_dir / f"{measure_id}.json"
        with open(file_path, "w") as f:
            f.write(measure.json(indent=2))
            
        # Add the Measure to the Bundle
        bundle_entry = BundleEntry(
            fullUrl=measure.url,
            resource=measure
        )
        bundle.entry.append(bundle_entry)
        
    # Save the master Bundle
    bundle_path = project_root / "data" / "fhir" / "master_measures_bundle.json"
    with open(bundle_path, "w") as f:
        f.write(bundle.json(indent=2))
            
    print(f"✅ Successfully generated and saved {len(indicators)} individual FHIR Measure resources!")
    print(f"✅ Created a Master FHIR Bundle containing all Measures at: {bundle_path.name}")
    print(f"📁 Output Directory: {output_dir}/")

if __name__ == "__main__":
    generate_all_measures()
