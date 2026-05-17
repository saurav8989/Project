# Phase 6: FHIR Standardization Architecture

## A. Learn FHIR Structure
Because the DHIS2 Immunization dataset consists of **monthly aggregate data** (total counts per district) rather than individual patient-level records, standard FHIR `Immunization` resources cannot be used. Instead, the architecture utilizes the **Public Health Measure Reporting Framework**, relying on two interconnected HL7 FHIR resources:

### 1. `Measure` Resource (The Blueprint)
The `Measure` resource is a definitional artifact. It formally defines *what* is being evaluated without holding any specific clinical data or numbers. For this pipeline, a unique `Measure` acts as the computational blueprint for each vaccine, defining:
* **Numerator:** The raw dose count administered.
* **Denominator:** The target population (Surviving Infants).

### 2. `MeasureReport` Resource (The Evaluated Data)
The `MeasureReport` resource is an evaluative artifact. It references a `Measure` blueprint and populates it with the actual numerical data for a specific time period and location.
* In this pipeline, each row in the DHIS2 dataset (representing one month) will generate a corresponding `MeasureReport` containing the actual integer values for the Numerator, Denominator, and the calculated Score (Coverage %).

---

## B. Define Mapping Table
The following table serves as the semantic mapping between the raw DHIS2 indicators and the FHIR Measure definitions. This mapping dictates how the `Cleaned_Data.csv` columns are structurally translated into HL7 JSON standards.

| DHIS2 Indicator | FHIR Measure ID | Numerator (Dose Count) | Denominator (Target Pop.) |
| :--- | :--- | :--- | :--- |
| **BCG Coverage** | `measure-bcg` | BCG (Col 2) | Surviving Infants (Monthly) |
| **Rota 1st Coverage** | `measure-rota1` | Rota 1st (Col 3) | Surviving Infants (Monthly) |
| **Rota 2nd Coverage** | `measure-rota2` | Rota 2nd (Col 4) | Surviving Infants (Monthly) |
| **OPV 1st Coverage** | `measure-opv1` | OPV 1st (Col 5) | Surviving Infants (Monthly) |
| **OPV 2nd Coverage** | `measure-opv2` | OPV 2nd (Col 6) | Surviving Infants (Monthly) |
| **OPV 3rd Coverage** | `measure-opv3` | OPV 3rd (Col 7) | Surviving Infants (Monthly) |
| **fIPV 1st Coverage**| `measure-fipv1` | fIPV 1st (Col 8) | Surviving Infants (Monthly) |
| **fIPV 2nd Coverage**| `measure-fipv2` | fIPV 2nd (Col 9) | Surviving Infants (Monthly) |
| **PCV 1st Coverage** | `measure-pcv1` | PCV 1st (Col 10) | Surviving Infants (Monthly) |
| **PCV 2nd Coverage** | `measure-pcv2` | PCV 2nd (Col 11) | Surviving Infants (Monthly) |
| **PCV 3rd Coverage** | `measure-pcv3` | PCV 3rd (Col 12) | Surviving Infants (Monthly) |
| **Penta 1st Coverage**| `measure-penta1`| Penta 1st (Col 13) | Surviving Infants (Monthly) |
| **Penta 2nd Coverage**| `measure-penta2`| Penta 2nd (Col 14) | Surviving Infants (Monthly) |
| **Penta 3rd Coverage**| `measure-penta3`| Penta 3rd (Col 15) | Surviving Infants (Monthly) |
| **MR 1st Coverage** | `measure-mr1` | MR 1st (Col 16) | Surviving Infants (Monthly) |
| **MR 2nd Coverage** | `measure-mr2` | MR 2nd (Col 17) | Surviving Infants (Monthly) |
| **JE Coverage** | `measure-je` | JE (Col 18) | Surviving Infants (Monthly) |
| **TCV Coverage** | `measure-tcv` | TCV (Col 19) | Surviving Infants (Monthly) |

*Note: The calculated `Score` in the resulting `MeasureReport` will be equivalent to the traditional Coverage Formula: `(Numerator / Denominator) * 100`.*
