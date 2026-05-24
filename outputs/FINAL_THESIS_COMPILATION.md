# National Childhood Immunization Analytics and Data Quality Assessment: A FHIR Interoperability Approach

**Master's Thesis**  
Masters in Health Informatics  
Submitted: May 2026

**Author:** Saurav Paudel  
**Email:** prastabpaudel1234@gmail.com

---

## Table of Contents

1. [Abstract](#abstract)
2. [Introduction](#introduction)
3. [Background and Literature Review](#background)
4. [Dataset Description](#dataset)
5. [Methodology](#methodology)
   - Phase 1: Data Ingestion and Profiling
   - Phase 2: Data Quality Assessment
   - Phase 3: Rule-Based Validation
   - Phase 4: Data Cleaning
   - Phase 5: FHIR Architectural Mapping
   - Phase 6: FHIR Resource Generation
   - Phase 7: FHIR Validation
   - Phase 8: FHIR Implementation Guide
   - Phase 9: Reference API Development
   - Phase 10: Clinical Analytics Dashboard
6. [Results and Analysis](#results)
7. [Implementation Details](#implementation)
8. [Discussion](#discussion)
9. [Conclusion and Future Work](#conclusion)
10. [References](#references)
11. [Appendices](#appendices)

---

## 1. Abstract {#abstract}

This thesis presents an end-to-end computational framework for standardizing five fiscal years of aggregate public health data from Nepal's District Health Information Software 2 (DHIS2) into the globally recognized HL7 Fast Healthcare Interoperability Resources (FHIR) R4 standard. The study focuses on the Kavrepalanchok district of Bagmati Province, Nepal, covering 60 monthly immunization reports across 18 distinct vaccine indicators from fiscal year 2077/78 through 2081/82 (approximately 2020–2025 in the Gregorian calendar).

A multi-stage automated data quality assessment (DQA) engine was engineered using Python to detect three classes of data integrity failures: (1) coverage anomalies where reported vaccination rates exceeded 100% of the target population (728 instances detected), (2) logical drop-out violations where subsequent dose counts impossibly exceeded prior dose counts (255 instances detected), and (3) missing data indicators for TCV (Typhoid Conjugate Vaccine), which was not universally introduced across the reporting period (20 missing records).

Following DQA, the sanitized dataset was semantically mapped to the HL7 FHIR Public Health Measure Reporting Framework. A total of 18 FHIR `Measure` blueprint resources and 1,080 FHIR `MeasureReport` evaluative resources were computationally generated using the `fhir.resources` Python library. A custom FHIR extension (`nepali-fiscal-period`) was engineered to preserve the Bikram Sambat calendar context without loss of clinical fidelity. All 1,080 generated payloads achieved 100% structural and logical validation against the HL7 R4 schema.

The interoperability of the FHIR dataset was demonstrated through two production-grade software components: a FastAPI REST reference server exposing FHIR-compliant HTTP endpoints, and an interactive Streamlit clinical analytics dashboard consuming those endpoints to render real-time epidemiological and DQA visualizations. A formal FHIR Implementation Guide (IG), authored in FHIR Shorthand (FSH) and compiled via SUSHI, was published and is publicly accessible at [https://saurav8989.github.io/Project/](https://saurav8989.github.io/Project/).

**Keywords:** FHIR R4, DHIS2, Health Interoperability, Immunization Data Quality, Nepal, MeasureReport, HL7, Public Health Informatics

---

## 2. Introduction {#introduction}

### 2.1 Background and Motivation

Immunization programs are widely recognized as one of the most cost-effective public health interventions available to low- and middle-income countries. Nepal, a landlocked nation with a complex geographic terrain and a tiered health system administered by provincial and local governments, relies on the District Health Information Software 2 (DHIS2) platform to aggregate and report monthly immunization data from health facilities across its 77 districts. Despite the widespread adoption of DHIS2 as a national health management information system (HMIS), the raw data it produces frequently suffers from structural inconsistencies, missing values, mathematical anomalies, and calendar localization challenges that severely limit its utility for regional or international health analytics.

A fundamental problem is the lack of interoperability. Data stored natively in DHIS2 is not machine-readable by external systems without bespoke integration work. Clinical decision-support tools, surveillance dashboards, and research platforms built on international standards cannot consume this data directly. This creates data silos that impede evidence-based health policy, delay outbreak response, and prevent Nepal's health data from contributing to global immunization benchmarks maintained by organizations such as the WHO and UNICEF.

HL7 FHIR (Fast Healthcare Interoperability Resources) Release 4 has emerged as the preeminent global standard for health data exchange. By encoding clinical data in well-defined, machine-readable JSON structures with standardized terminologies and REST-based access patterns, FHIR eliminates these integration barriers. However, converting legacy aggregate reporting data — particularly data encoded in Nepali Bikram Sambat calendar format — to FHIR is a non-trivial technical challenge that requires careful architectural decisions.

### 2.2 Problem Statement

There is no established, open-source pipeline for converting Nepal's DHIS2 immunization aggregate data into HL7 FHIR R4 standard resources. Furthermore, the raw data contains significant data quality deficiencies that, if not formally documented and handled, would propagate into any derived FHIR dataset, compromising clinical decision-making built upon it.

### 2.3 Objectives

This project addresses the above gap through four primary objectives:

1. **Data Quality Assessment:** Programmatically audit five fiscal years of raw DHIS2 aggregate immunization data from Kavrepalanchok district to formally identify, quantify, and document structural, logical, and statistical data quality failures using automated Python-based DQA algorithms.

2. **FHIR Standardization:** Transform the assessed dataset into strictly validated HL7 FHIR R4 `Measure` and `MeasureReport` resources that preserve the full clinical and administrative context of the original DHIS2 records — including Nepali calendar metadata and missing data semantics — without loss of fidelity.

3. **Formal Standards Publication:** Author and publish a formal FHIR Implementation Guide (IG) using FHIR Shorthand (FSH) and the SUSHI compiler to formally specify the constraints, extensions, and vocabulary that govern the generated FHIR payloads, making the architecture reproducible and internationally reviewable.

4. **Operational Demonstration:** Deploy a FHIR-native REST API and an interactive clinical analytics dashboard to prove that the standardized FHIR data can support real-time epidemiological analysis and data quality auditing by end-users without any knowledge of the underlying file structure.

### 2.4 Significance and Contribution

This work makes three original contributions to health informatics in the Nepalese context:

- The first formally validated, open-source DHIS2-to-FHIR transformation pipeline for aggregate immunization data using the Bikram Sambat calendar.
- An automated DQA engine whose findings quantify the magnitude of data quality issues in Nepal's DHIS2 reporting infrastructure, providing an evidence base for systemic reporting reforms.
- A publicly accessible FHIR Implementation Guide establishing a reusable technical specification that any Nepali district health office or HMIS integrator can adopt to achieve FHIR compliance.

---

## 3. Background and Literature Review {#background}

### 3.1 Nepal's National Immunization Program

Nepal's National Immunization Program (NIP), administered by the Ministry of Health and Population (MoHP) through the Child Health Division, targets all children below the age of one year (and some beyond) for a schedule of government-funded vaccines. The program covers BCG (Bacille Calmette-Guérin) for tuberculosis, Oral Polio Vaccine (OPV), Inactivated Polio Vaccine (IPV/fIPV), Rotavirus Vaccine (Rota), Pentavalent Vaccine (Penta — combining DTP, HepB, Hib), Pneumococcal Conjugate Vaccine (PCV), Measles-Rubella Vaccine (MR), Japanese Encephalitis Vaccine (JE), and the more recently introduced Typhoid Conjugate Vaccine (TCV).

Data from health posts, primary health care centers, and hospitals is reported monthly to the District Health Office, which aggregates and uploads it to the DHIS2 system. The reporting unit is the district, and the target population denominator used for coverage calculations is the estimate of surviving infants for that month.

### 3.2 DHIS2 and Its Limitations

DHIS2 is an open-source HMIS platform developed by the HISP Centre at the University of Oslo and is deployed in over 70 countries. While DHIS2 provides powerful aggregate reporting capabilities, it has well-documented interoperability limitations. Its native data model is not aligned with HL7 FHIR. Data export is primarily available in flat CSV or DHIS2-proprietary JSON formats, neither of which can be directly consumed by FHIR-compliant clinical systems. Previous studies have explored DHIS2-to-FHIR bridges (e.g., the DHIS2-FHIR adapter project), but none specifically address the Nepalese context with its Bikram Sambat calendar and the measurement reporting framework.

### 3.3 HL7 FHIR R4 and the Measure Reporting Framework

HL7 FHIR Release 4 (published in 2019) is the current normative release of the FHIR standard. Unlike earlier releases, R4 provides a mature and stable specification for `Measure` and `MeasureReport` resources, which form the core of the FHIR Quality Reporting Framework. The `Measure` resource encodes the computational logic (what is being measured, how numerator and denominator are defined), while the `MeasureReport` encodes the actual numerical results for a specific population and time period.

This Measure/MeasureReport pattern is uniquely suited to aggregate public health data like DHIS2 outputs, making it the architecturally correct choice over individual `Immunization` resources, which are designed for patient-level records.

### 3.4 Data Quality in Public Health Reporting

Data quality assessment in health management information systems has been the subject of substantial research. The WHO Data Quality Review Toolkit identifies four primary dimensions: completeness, timeliness, consistency, and accuracy. This project operationalizes three of these dimensions — completeness (facility and indicator-level), consistency (drop-out logic violations), and accuracy (coverage outlier detection) — through automated Python algorithms, producing machine-readable audit trails aligned with international DQA frameworks.

---

## 4. Dataset Description {#dataset}

### 4.1 Source and Scope

The primary dataset was extracted from Nepal's DHIS2 HMIS for **Kavrepalanchok district**, Bagmati Province (District Code: 31). The dataset spans **five complete Nepali fiscal years**: 2077/78 through 2081/82, corresponding approximately to the Gregorian period of July 2020 through July 2025. Each fiscal year in Nepal runs from Shrawan (Month 1) through Asar (Month 12), yielding 12 monthly records per year and **60 total records** in the dataset.

### 4.2 Structure

The raw dataset (`Data.xlsx`) contains **60 rows and 31 columns** with the following structure:

| Column Group | Fields | Count |
|---|---|---|
| Administrative metadata | SN, Fiscal Year, Month No., Month (EN), Month (NP), District, Province, Dist. Code | 8 |
| Vaccine dose counts | BCG through TCV (18 indicators) | 18 |
| Population denominators | Surviving Infants (Annual), Surviving Infants (Monthly) | 2 |
| Facility reporting | Facilities Expected, Facilities Reported, Facilities Not Reported | 3 |

**Table 1: Vaccine Indicators in the Dataset**

| Vaccine | Abbreviation | Doses | FHIR Measure ID |
|---|---|---|---|
| BCG (Tuberculosis) | BCG | 1 | `measure-bcg` |
| Rotavirus | Rota | 2 | `measure-rota1`, `measure-rota2` |
| Oral Polio Vaccine | OPV | 3 | `measure-opv1`, `measure-opv2`, `measure-opv3` |
| Fractional Inactivated Polio Vaccine | fIPV | 2 | `measure-fipv1`, `measure-fipv2` |
| Pneumococcal Conjugate Vaccine | PCV | 3 | `measure-pcv1`, `measure-pcv2`, `measure-pcv3` |
| Pentavalent (DTP-HepB-Hib) | Penta | 3 | `measure-penta1`, `measure-penta2`, `measure-penta3` |
| Measles-Rubella | MR | 2 | `measure-mr1`, `measure-mr2` |
| Japanese Encephalitis | JE | 1 | `measure-je` |
| Typhoid Conjugate Vaccine | TCV | 1 | `measure-tcv` |

### 4.3 Initial Data Quality Observations

Upon initial profiling, three data quality issues were immediately observed:

1. **TCV missing values:** 20 of 60 records (33.3%) had `NaN` values for TCV dose counts, reflecting the fact that TCV was not introduced in Kavrepalanchok until partway through the reporting period.
2. **Facility reporting nulls:** `Facilities Reported` and `Facilities Not Reported` contained 7 missing values each, representing months with incomplete administrative records.
3. **Float type contamination:** Columns that are conceptually integers (`TCV`, `Facilities Reported`, `Facilities Not Reported`) were loaded as `float64` by pandas due to the presence of `NaN` values in those columns. All other vaccine columns were correctly typed as `int64`.
4. **No duplicate rows** were detected across all 60 records.

---

## 5. Methodology {#methodology}

The project was executed as a 10-phase sequential pipeline. Each phase produces well-defined artifacts that serve as inputs to the subsequent phase.

```
Phase 1: Data Ingestion & Profiling
        ↓
Phase 2: Data Quality Assessment (DQA)
        ↓
Phase 3: Rule-Based Validation (Pandera)
        ↓
Phase 4: Data Cleaning
        ↓
Phase 5: FHIR Architectural Mapping
        ↓
Phase 6: FHIR Resource Generation
        ↓
Phase 7: FHIR Validation
        ↓
Phase 8: FHIR Implementation Guide (FSH/SUSHI)
        ↓
Phase 9: Reference API Development (FastAPI)
        ↓
Phase 10: Clinical Analytics Dashboard (Streamlit)
```

---

### Phase 1: Data Ingestion and Profiling

**Script:** `scripts/data_loading/load_data.py`, `scripts/data_loading/inspect_data.py`

The raw dataset was ingested from `Data.xlsx` using the `pandas` library. An automated profiling script was executed to establish the baseline characteristics of the dataset prior to any transformation:

- **Shape:** 60 rows × 31 columns confirmed.
- **Column inventory:** All 31 columns catalogued with data types, null counts, and value ranges.
- **Missing value detection:** TCV (20 nulls), Facilities Reported (7 nulls), Facilities Not Reported (7 nulls).
- **Duplicate detection:** Zero duplicate rows found.
- **Vaccine column identification:** 18 vaccine indicator columns automatically identified for downstream processing.

**Output Artifact:** `outputs/profiling_report.txt`

---

### Phase 2: Data Quality Assessment Engine

**Script:** `scripts/quality_assessment/completeness.py`, `scripts/quality_assessment/consistency_checks.py`, `scripts/quality_assessment/outlier_detection.py`

A three-component DQA engine was constructed corresponding to the three primary quality dimensions relevant to immunization aggregate data:

#### 2A. Completeness Assessment

**Facility Reporting Completeness** was calculated as:

```
Reporting Completeness (%) = (Facilities Reported / 161) × 100
```

where 161 represents the total number of expected reporting health facilities in Kavrepalanchok district. This metric was computed at both fiscal year and monthly granularity to reveal temporal trends and seasonal patterns.

**Indicator Completeness** was calculated per vaccine column as:

```
Indicator Completeness (%) = (Non-null Values / 60) × 100
```

A facility completeness heatmap was generated to visualize the reporting compliance pattern across months and fiscal years.

**Output Artifacts:** `outputs/completeness_report.txt`, `outputs/facility_completeness_heatmap.png`

#### 2B. Internal Consistency Checks

Internal consistency was evaluated using the **immunization drop-out rule**: for multi-dose vaccines, the count of doses administered for a later dose can never logically exceed the count for an earlier dose within the same reporting period. This is because a child who receives Dose 3 must necessarily have received Dose 1 and Dose 2.

The following rules were enforced across all 60 monthly records:

| Vaccine | Rules |
|---|---|
| Rota | Rota1 ≥ Rota2 |
| OPV | OPV1 ≥ OPV2 ≥ OPV3 |
| fIPV | fIPV1 ≥ fIPV2 |
| PCV | PCV1 ≥ PCV2 ≥ PCV3 |
| Penta | Penta1 ≥ Penta2 ≥ Penta3 |
| MR | MR1 ≥ MR2 |

Violations were recorded with the full row context (Fiscal Year, Month, District, dose pair, actual counts, and the magnitude of violation).

**Output Artifacts:** `outputs/consistency_report.txt`, `outputs/consistency_violations.csv`, `outputs/consistency_monthly_trend.png`

#### 2C. Plausibility and Outlier Detection

**Coverage Outlier Detection** applied the standard immunization coverage formula:

```
Coverage (%) = (Doses Administered / Surviving Infants Monthly) × 100
```

Any record where Coverage > 100% was flagged as an impossible anomaly, since more children cannot be vaccinated than exist in the target population. While such values can arise from legitimate causes (e.g., out-of-district children receiving vaccines in a higher-capacity facility), they represent a denominator problem that compromises standard coverage reporting.

**Statistical Outlier Detection** applied two complementary algorithms to the raw dose count columns:
- **Z-Score method:** Records with |Z| > 3 were flagged as extreme statistical outliers.
- **IQR method:** Records outside [Q1 − 1.5×IQR, Q3 + 1.5×IQR] were flagged as potential outliers.

Outliers were categorized as either **Spikes** (sudden upward surges) or **Drops** (sudden downward collapses) in dose counts.

**Output Artifacts:** `outputs/plausibility_report.txt`, `outputs/coverage_over_100.csv`, `outputs/statistical_outliers.csv`, `outputs/outliers_boxplots.png`, `outputs/outliers_trend.png`

---

### Phase 3: Rule-Based Validation (Pandera)

**Script:** `scripts/quality_assessment/schema_validation.py`

A formal schema validation was conducted using the **Pandera** library, which allows for declarative DataFrame schema specifications. This phase applied the same drop-out logic rules as Phase 2 but in a formal, machine-enforced schema framework that can be audited and reproduced.

The schema enforced the following constraints:
- `Month No.` must be an integer in range [1, 12].
- `Surviving Infants (Monthly)` must be ≥ 0.
- All vaccine dose columns must be ≥ 0.
- Drop-out logic rules (Penta1 ≥ Penta2 ≥ Penta3, OPV1 ≥ OPV2 ≥ OPV3, etc.) enforced as cross-column checks.

The Pandera validator returned **4,520 total violations**, a higher count than the consistency check in Phase 2 because Pandera validates each failing rule against each row independently (row-level cardinality), whereas Phase 2 counted unique violation events.

Critically, **no data modification was made** at this stage. The validator was run in an audit-only mode, and the original DataFrame was passed through unchanged to the FHIR mapping pipeline. This decision was deliberate: the philosophy of this pipeline is to preserve raw aggregate counts as-is and encode the data quality findings as metadata (through FHIR extensions and `DataAbsentReason` codes), rather than silently correcting the data.

**Output Artifact:** `outputs/rule_based_validation_report.txt`, `outputs/pandera_validation_errors.csv`

---

### Phase 4: Data Cleaning

**Script:** `scripts/data_cleaning/clean_data.py`

A targeted, minimal data cleaning pipeline was executed with explicit handling rules for each identified issue:

1. **Missing Facility Reporting Data:** Seven `NaN` values in `Facilities Reported` were filled with `0` (no facilities reported). The corresponding `Facilities Not Reported` nulls were filled with `161` (all 161 expected facilities failed to report). This preserves the constraint that `Reported + Not Reported = Expected`.

2. **Missing TCV Data:** All 20 `NaN` values in the TCV column were replaced with `0`. This is a clinically accurate representation: a zero value indicates "vaccine not yet introduced / not applicable" for those months, which is semantically distinct from "vaccine administered but not reported." This distinction is preserved at the FHIR layer via the `DataAbsentReason` extension (see Phase 6).

3. **Data Type Standardization:** All `float64` vaccine and facility columns were dynamically cast to `int64` to reflect the reality that partial vaccine doses do not exist in aggregate reporting.

4. **Outlier Preservation (Intentional):** Coverage values exceeding 100% were explicitly left untouched. The drop-out logic violations were also left untouched. This decision reflects the principle that a DQA pipeline should surface and formally annotate data anomalies, not silently discard them — particularly for a research context where the magnitude of the anomalies is itself a finding.

**Output Artifact:** `data/processed/Cleaned_Data.csv`, `outputs/data_cleaning_report.txt`

---

### Phase 5: FHIR Architectural Mapping

**Script:** `scripts/fhir_mapping/generate_measures.py`

Before generating any FHIR resources, a formal semantic mapping was designed to translate DHIS2 concepts to FHIR concepts. This mapping is the intellectual core of the pipeline.

**Why Measure/MeasureReport, not Immunization?**

The FHIR `Immunization` resource is designed for **patient-level records** — a single vaccination event for a named individual. The DHIS2 dataset contains **aggregate monthly counts** — total doses administered across all children in a district for a given month, with no individual patient identifiers. Using `Immunization` resources for this data would be semantically incorrect.

The FHIR **Public Health Measure Reporting Framework** (Measure + MeasureReport) is the correct pattern for aggregate health reporting. A `Measure` resource defines the computational logic (numerator formula, denominator formula, scoring type), and a `MeasureReport` resource instantiates that logic with actual numerical results for a specific period.

**Semantic Mapping Table**

| DHIS2 Concept | FHIR Concept |
|---|---|
| Vaccine indicator (e.g., "BCG") | `Measure` resource (1 per vaccine) |
| Dose count (Numerator) | `MeasureReport.group.population[numerator].count` |
| Surviving Infants (Denominator) | `MeasureReport.group.population[denominator].count` |
| Coverage % | `MeasureReport.group.measureScoreQuantity.value` |
| Fiscal Year + Month | Custom `nepali-fiscal-period` FHIR Extension |
| Gregorian proxy period | `MeasureReport.period` (start/end dates) |
| Missing data (zero count) | `DataAbsentReason` FHIR Extension on population |

---

### Phase 6: FHIR Resource Generation

**Scripts:** `scripts/fhir_mapping/generate_measures.py`, `scripts/fhir_mapping/generate_measure_reports.py`

All FHIR resources were generated programmatically using the `fhir.resources` Python library, which provides Pydantic-backed Python classes that mirror the HL7 R4 schema.

#### 6A. Measure Resource Generation (18 resources)

For each of the 18 vaccine indicators, a `Measure` resource was generated as a definitional blueprint. Each `Measure` contains:
- A unique canonical URL: `http://example.org/fhir/Measure/measure-{vaccine_id}`
- A machine-readable `name` and human-readable `title`
- A population group defining three populations using the standard `http://terminology.hl7.org/CodeSystem/measure-population` coding:
  - `initial-population`: Surviving Infants (Monthly)
  - `denominator`: Surviving Infants (Monthly)
  - `numerator`: Doses Administered
- CQL (Clinical Quality Language) expression stubs to formally declare the population criteria

**Output Artifacts:**
- 18 individual JSON files: `data/fhir/measures/measure-{id}.json`
- 1 master FHIR Bundle: `data/fhir/master_measures_bundle.json`

#### 6B. MeasureReport Resource Generation (1,080 resources)

For each of the 60 monthly records in `Cleaned_Data.csv` and each of the 18 vaccines, one `MeasureReport` resource was generated — yielding **1,080 MeasureReport resources** in total.

Each `MeasureReport` contains:

**Standard FHIR Fields:**
- `id`: Unique identifier (e.g., `measure-bcg-row-1`)
- `status`: `complete`
- `type`: `summary` (aggregate report)
- `measure`: Canonical reference to the parent `Measure` resource
- `period`: ISO-8601 Gregorian date range (start/end) serving as a proxy for timeline charting
- Population group with integer counts for numerator, denominator, and initial population
- `measureScoreQuantity`: Pre-calculated coverage percentage with unit `%`

**Custom Extension — `nepali-fiscal-period`:**
Because DHIS2 uses the Bikram Sambat (BS) calendar and Nepali month names, which do not align with ISO-8601, a custom FHIR Extension was engineered with the canonical URL `http://example.org/fhir/StructureDefinition/nepali-fiscal-period`. This extension carries four sub-extension values:
- `fiscalYear`: Nepali fiscal year string (e.g., `"2077/78"`)
- `monthEnglish`: English transliteration of month (e.g., `"Shrawan"`)
- `monthNepali`: Nepali Devanagari script month name (e.g., `"श्रावण"`)
- `district`: District name (e.g., `"Kavrepalanchok"`)

This extension ensures that the FHIR resources carry the ground-truth temporal context without any calendar conversion loss.

**Missing Data Handling — `DataAbsentReason` Extension:**
For TCV records where the dose count was zero (representing months before TCV introduction), the `count` integer was **omitted** from the numerator population rather than set to zero. In its place, the FHIR `DataAbsentReason` extension was applied:
- TCV zero counts: `not-applicable` (vaccine not yet introduced in that period)
- Other vaccine zero counts: `unknown` (data not reported by facilities)

This is a critical clinical fidelity decision: a missing count in FHIR carries a different semantic meaning than a zero count. A zero implies "zero doses were given," whereas `DataAbsentReason` correctly communicates "this data point was not recorded."

**Output Artifacts:**
- 60 month-wise directories: `data/fhir/monthwise_measure_report/{fiscal_year_month}/`
- 1,080 individual MeasureReport JSON files distributed across these directories
- 60 month-specific FHIR Bundles (one per directory)
- 1 master FHIR Bundle: `data/fhir/master_measurereports_bundle.json`

---

### Phase 7: FHIR Validation

**Script:** `scripts/fhir_mapping/validate_fhir.py`

A two-level automated validation was executed against all 1,098 generated FHIR resources (18 Measures + 1,080 MeasureReports):

**Level 1 — Structural & Schema Validation:**
Every JSON file was re-parsed using the `fhir.resources` Python library. Because this library uses Pydantic validation models internally, any missing required field, incorrect data type, or invalid FHIR keyword causes an immediate `ValidationError`. Passing this parse step is equivalent to passing a schema conformance check against the HL7 R4 specification.

**Level 2 — Logical & Mathematical Consistency:**
Custom Python logic performed two additional audits beyond structural validation:
1. **Score Accuracy Audit:** For each `MeasureReport`, the coverage percentage was independently recalculated as `(numerator / denominator) × 100` and compared against the `measureScoreQuantity.value` stored in the resource. Any discrepancy would indicate a generation error.
2. **DataAbsentReason Compliance Audit:** For every population where the `count` field was omitted, the script verified that a valid `DataAbsentReason` extension was present. Populations missing both a count and the required extension would be flagged as clinically non-compliant.

**Output Artifact:** `outputs/fhir_validation_report.txt`

---

### Phase 8: FHIR Implementation Guide (FSH and SUSHI)

To elevate the project from a local data transformation pipeline to a formally publishable, internationally reviewable health informatics specification, a complete **FHIR Implementation Guide (IG)** was authored using **FHIR Shorthand (FSH)** — a domain-specific language for authoring FHIR content — and compiled using the **SUSHI** (SUSHI Unshortens ShortHand Inputs) toolchain.

**Components of the Implementation Guide:**

1. **Custom Terminology Bindings:** 
   - `VaccineIndicators`: A formal `CodeSystem` and `ValueSet` enumerating the 18 valid vaccine indicator codes (e.g., `bcg`, `penta-1`).
   - `BikramSambatMonths`: A "Gold Standard" terminology artifact comprising a `CodeSystem` (`BikramSambatMonthsCS`) and `ValueSet` (`BikramSambatMonthsVS`) defining the 12 Nepali calendar months. This is directly bound to the `valueString` of the custom calendar extension.

2. **Custom Extension (`NepaliFiscalYear`):** The `nepali-fiscal-period` extension used in the generated resources was formally specified as an FSH `Extension` definition. The month string is rigidly bound to the `BikramSambatMonthsVS` ValueSet, ensuring native FHIR validation of DHIS2 string values.

3. **Resource Profiles:**
   - `NepalImmunizationMeasure`: A FHIR `Profile` constraining the standard `Measure` resource.
   - `NepalImmunizationMeasureReport`: A FHIR `Profile` on `MeasureReport` mandating the `nepali-fiscal-period` extension and geographical subject references.

4. **Representative FHIR Instances:** Rather than overloading the IG Publisher with all 1,080 generated production records, perfectly conforming "Gold Standard" examples were authored natively in FSH (a `Location` for Kavrepalanchok, an `Organization` for DHO Kavre, and an exemplary `MeasureReport` for Penta 1). These serve as the canonical reference models within the IG.

5. **SUSHI Compilation:** The FSH source files were compiled by the SUSHI CLI tool, generating hundreds of machine-readable `StructureDefinition` JSON files representing the profiles, extensions, and terminology bindings.

6. **CI/CD Publication:** An automated CI/CD pipeline was established using **GitHub Actions** to continuously compile the IG using the official **HL7 IG Publisher** and deploy it as a static website via GitHub Pages.

**Published URL:** [https://saurav8989.github.io/Project/](https://saurav8989.github.io/Project/)

---

### Phase 9: Reference API Development

**Script:** `scripts/api/fhir_server.py`

A lightweight FHIR-compliant REST API was built using the **FastAPI** Python framework and served by the **Uvicorn** ASGI server. The purpose of this server is twofold: to serve as a realistic simulation of a FHIR server endpoint that any standard FHIR client could consume, and to act as the data source for the analytics dashboard.

**API Endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check — returns server status |
| `GET` | `/fhir/Measure` | Returns FHIR Bundle of all 18 Measure blueprints |
| `GET` | `/fhir/Measure/{measure_id}` | Returns a single Measure by ID (e.g., `measure-bcg`) |
| `GET` | `/fhir/MeasureReport` | Returns FHIR Bundle of all 1,080 MeasureReports |
| `GET` | `/fhir/MeasureReport/{report_id}` | Returns a single MeasureReport by ID |

The server loads the pre-compiled master bundle JSON files from disk for bulk requests and uses recursive directory search (`rglob`) across the 60 month-wise subdirectories for individual resource lookups. FastAPI automatically generates interactive OpenAPI (Swagger) documentation accessible at `/docs`.

**Access:** `http://127.0.0.1:8000`  
**Documentation:** `http://127.0.0.1:8000/docs`

---

### Phase 10: Clinical Analytics Dashboard

**Script:** `scripts/api/dashboard.py`

An interactive clinical analytics dashboard was built using **Streamlit** with **Plotly** visualizations. The dashboard fetches all data exclusively via HTTP GET requests to the FHIR API — it does not read any JSON or CSV files directly — demonstrating true end-to-end FHIR interoperability.

**Data Pipeline within the Dashboard:**
1. `fetch_fhir_data()` sends a `GET /fhir/MeasureReport` request to the API.
2. Each entry in the returned FHIR Bundle is parsed: the `nepali-fiscal-period` extension is traversed for calendar context, populations are extracted by their `coding.code` values, and `DataAbsentReason` extensions are detected as missing data flags.
3. The parsed data is structured into a Pandas DataFrame with columns: `Date`, `Fiscal_Year`, `Month`, `Vaccine_ID`, `Doses_Administered`, `Target_Population`, `Coverage_Percentage`, `Is_Absent`.
4. A secondary `fetch_facility_data()` function reads `Cleaned_Data.csv` directly to compute facility reporting rates, as this field is not encoded in the FHIR MeasureReport schema.
5. Both functions use `@st.cache_data(ttl=600)` to cache results for 10 minutes.

**Dashboard Sections:**

*Landing Page (No filter selected):*
- **Four global KPI cards:** Total FHIR Records, Total Coverage Outliers (>100%), Total Logical Violations, and Average System-wide Dropout Rate — providing an immediate macro-level health system summary without any filter selection.
- Average coverage trend line chart across all vaccines over the 60-month period, summarizing the national immunization trajectory including the COVID-19 impact period.
- Data quality donut chart: Clean Data vs. Coverage Outliers vs. Missing Data (TCV), derived from the `DataAbsentReason` extension parsed directly from FHIR resources.
- Horizontal bar chart of total doses administered per vaccine family over 5 years.
- **System-wide Dropout bar chart:** A dedicated horizontal bar chart displaying the 5-year aggregate dropout rates for all multi-dose vaccine families (Penta, OPV, PCV, Rota, MR, fIPV), enabling instant cross-vaccine retention comparison at the national level.

*Drill-Down View (Vaccine Family + Fiscal Year selected):*
- **Section 1 — Executive Metrics:** Data Completeness %, Average Vaccine Coverage %, Facility Reporting Rate %, and — exclusively for multi-dose vaccines — an **Overall Dropout Rate %** KPI dynamically calculated as the retention loss between Dose 1 and the final dose across the selected period.
- **Section 2 — Epidemiological Analytics:** Longitudinal coverage trend line chart (coloured by dose for multi-dose vaccines); Clinical dropout bar chart showing total cumulative doses per dose number; and for multi-dose vaccines, an advanced **Dropout & Retention Analysis** module that plots the longitudinal dropout rate over the full 60-month period between Dose 1 and the final dose, revealing whether retention is improving or degrading over time.
- **Section 3 — Data Quality Assessment:** Consistency violations table (dose logic errors per month), Coverage outliers table (records > 100%). The consistency check is dynamically omitted for single-dose vaccines where the drop-out rule is not applicable.
- **Raw Data Expander:** Collapsible view of the full parsed FHIR DataFrame for the current selection.

**Access:** `http://localhost:8501`

---

## 6. Results and Analysis {#results}

### 6.1 Data Profiling Results

- **Dataset dimensions:** 60 rows × 31 columns
- **Duplicate records:** 0
- **Missing values:** TCV (20 records, 33.3%), Facilities Reported (7 records, 11.7%), Facilities Not Reported (7 records, 11.7%)
- **All 18 vaccine columns:** zero missing values (100% complete) except TCV

### 6.2 Completeness Assessment Results

**Table 2: Facility Reporting Completeness by Fiscal Year**

| Fiscal Year | Reporting Completeness (%) |
|---|---|
| 2077/78 | 75.21 |
| 2078/79 | 75.91 |
| 2079/80 | 86.34 |
| 2080/81 | 87.92 |
| 2081/82 | 87.80 |

The data shows a strong positive trend, with facility reporting improving by approximately 12.6 percentage points over the five-year period. The improvement was particularly pronounced between FY 2079/80 and FY 2080/81, suggesting a systemic policy or administrative intervention improved compliance.

**Table 3: Monthly Reporting Completeness (Average Across All 5 Years)**

| Month | Completeness (%) |
|---|---|
| Shrawan | 81.68 |
| Bhadra | 83.48 |
| Ashwin | 79.81 |
| Kartik | 81.49 |
| Mangsir | 85.22 |
| Poush | 75.16 |
| Magh | 84.16 |
| Falgun | 83.48 |
| Chaitra | 83.23 |
| Baishak | 88.35 |
| Jestha | 82.73 |
| Asar | 86.13 |

The month of **Poush** (mid-December to mid-January) consistently showed the lowest reporting compliance (75.16%), likely due to winter weather disruptions in a mountainous district. **Baishak** (mid-April to mid-May) showed the highest compliance (88.35%), coinciding with Nepal's New Year period when administrative focus on health reporting is elevated.

**Indicator Completeness:** All 17 non-TCV vaccine indicators achieved 100% completeness. TCV was 66.67% complete (40 of 60 records), reflecting phased introduction of the vaccine.

### 6.3 Consistency Check Results

**Table 4: Consistency Violations by Rule**

| Violated Rule | Violations |
|---|---|
| MR1 ≥ MR2 | 34 |
| Penta2 ≥ Penta3 | 32 |
| OPV2 ≥ OPV3 | 31 |
| PCV2 ≥ PCV3 | 30 |
| Penta1 ≥ Penta2 | 26 |
| PCV1 ≥ PCV2 | 26 |
| fIPV1 ≥ fIPV2 | 26 |
| OPV1 ≥ OPV2 | 25 |
| Rota1 ≥ Rota2 | 25 |
| **Total** | **255** |

255 consistency violations were detected across all multi-dose vaccine pairs. MR (Measles-Rubella) showed the highest violation rate, followed closely by Penta and OPV.

**Temporal Pattern:** Violations were heavily concentrated at the start (Shrawan: 34 violations) and end (Asar: 35 violations) of each fiscal year. This is a classic artifact of **year-boundary reporting errors** in aggregate HMIS systems, where facilities may report accumulated or adjusted counts when submitting year-start and year-end reports.

### 6.4 Outlier Detection Results

**Coverage Anomalies:** 728 instances of coverage > 100% were detected across all vaccines and months. Notable examples:
- BCG coverage reached **185.94%** in Ashwin 2077/78
- BCG coverage reached **184.15%** in Bhadra 2077/78

These extreme values indicate a fundamental denominator problem: the monthly surviving infant estimates used as the coverage denominator appear to be significantly understated relative to the actual vaccination catchment population. This may reflect children from neighbouring districts being vaccinated in Kavrepalanchok facilities.

**Statistical Outliers:** 20 extreme outliers were detected:
- 13 **Spikes**: sudden unexplained surges in single-month dose counts
- 7 **Drops**: sudden unexplained collapses in dose counts

### 6.5 Rule-Based Validation Results (Pandera)

The Pandera schema validator returned 4,520 violations across the dataset. The distribution was dominated by MR1 ≥ MR2 (1,039 row-level failures), Penta2 ≥ Penta3 (969 failures), and PCV2 ≥ PCV3 (911 failures). An additional 17 violations were flagged as `dtype('float64')` failures (the TCV column being float rather than integer due to NaN values).

### 6.6 FHIR Generation Results

| Resource Type | Generated | Description |
|---|---|---|
| `Measure` | 18 | One per vaccine indicator |
| `MeasureReport` | 1,080 | 60 months × 18 vaccines |
| Month-wise directories | 60 | One per fiscal month |
| Month-specific Bundles | 60 | One per month |
| Master Measures Bundle | 1 | All 18 Measures |
| Master MeasureReports Bundle | 1 | All 1,080 MeasureReports |
| **Total FHIR files** | **1,098** | |

### 6.7 FHIR Validation Results

**Table 5: FHIR Validation Summary**

| Resource | Audited | Structural Pass | Logical Pass | Status |
|---|---|---|---|---|
| `Measure` | 18 | 18 (100%) | N/A | ✅ PASS |
| `MeasureReport` | 1,080 | 1,080 (100%) | 1,080 (100%) | ✅ PASS |

All 1,080 MeasureReport resources:
- Passed the HL7 R4 structural schema validation (required fields present, correct data types, valid resource structure).
- Passed the mathematical consistency audit (calculated coverage % matched `measureScoreQuantity` in all cases).
- Correctly applied `DataAbsentReason` extension on all zero-count numerator populations.

---

## 7. Implementation Details {#implementation}

### 7.1 Technology Stack

| Component | Technology | Version |
|---|---|---|
| Data processing | Python, Pandas | 3.14, 2.x |
| Schema validation | Pandera | latest |
| FHIR resource generation | fhir.resources (Pydantic) | latest |
| REST API | FastAPI + Uvicorn | latest |
| Dashboard | Streamlit | latest |
| Visualization | Plotly Express | latest |
| IG authoring | FHIR Shorthand (FSH) | latest |
| IG compilation | SUSHI | latest |
| IG publishing | HL7 IG Publisher + GitHub Actions | latest |
| Version control | Git + GitHub | — |

### 7.2 Project Structure

```
Project/
├── data/
│   ├── raw/                    # Original Data.xlsx
│   ├── processed/              # Cleaned_Data.csv
│   └── fhir/
│       ├── measures/           # 18 Measure JSON files
│       ├── monthwise_measure_report/  # 60 directories, 1,080 MeasureReports
│       ├── master_measures_bundle.json
│       └── master_measurereports_bundle.json
├── scripts/
│   ├── data_loading/           # load_data.py, inspect_data.py
│   ├── quality_assessment/     # completeness.py, consistency_checks.py,
│   │                           # outlier_detection.py, schema_validation.py
│   ├── data_cleaning/          # clean_data.py
│   ├── fhir_mapping/           # generate_measures.py,
│   │                           # generate_measure_reports.py, validate_fhir.py
│   └── api/                    # fhir_server.py, dashboard.py
├── outputs/                    # All generated reports, charts, CSV exports
├── docs/                       # Data dictionary, architecture documentation
├── tests/                      # Automated tests
└── notebooks/                  # Jupyter exploration notebooks
```

### 7.3 Key Engineering Decisions

**Decision 1 — Aggregate-level FHIR pattern (Measure/MeasureReport over Immunization)**
The use of the FHIR Public Health Measure Reporting Framework rather than individual `Immunization` resources is the single most important architectural decision of the project. It reflects a correct reading of the FHIR specification: aggregate reporting data belongs in `MeasureReport`, not in `Immunization` bundles. This choice ensures that the generated resources can be queried and reasoned about by any FHIR-native quality reporting engine.

**Decision 2 — Preserve raw anomalies; encode them in FHIR metadata**
Rather than cleaning away the 728 coverage outliers and 255 consistency violations, these anomalies were preserved in the raw counts and their presence was formally documented in the DQA reports. This is methodologically correct for a research context and maintains the traceability of the source data.

**Decision 3 — Custom Nepali extension for calendar fidelity**
The Bikram Sambat calendar used in Nepal does not map cleanly to ISO-8601 dates. A custom FHIR extension was created to carry the authentic Nepali fiscal year and month strings, while a Gregorian proxy period was included in the standard `MeasureReport.period` field for compatibility with international charting and analytics tools.

**Decision 4 — DataAbsentReason over zero for missing TCV data**
Encoding missing TCV records as zero counts would have incorrectly implied that TCV was offered but zero doses were given. The `DataAbsentReason` extension (`not-applicable`) correctly communicates that the vaccine was not yet in the national program for that period — a critically different clinical signal.

**Decision 5 — API-first dashboard architecture**
The Streamlit dashboard was deliberately built to consume data only through the FHIR API, not from disk. This architectural constraint proves interoperability: the exact same API could be consumed by any external clinical or analytics system, and the dashboard itself becomes a proof-of-concept client.

**Decision 6 — Adaptive UI layout based on vaccine characteristics**
The dashboard dynamically changes its layout depending on whether the selected vaccine is single-dose (e.g., BCG, JE, TCV) or multi-dose (e.g., Penta, OPV, PCV). For single-dose vaccines, the consistency drop-out check is omitted (not applicable) and the dropout KPI and retention analysis module are hidden. For multi-dose vaccines, the full suite of dropout analytics — including the longitudinal Dropout & Retention Analysis chart and the Overall Dropout Rate KPI — is rendered. This adaptive approach avoids presenting clinically misleading metrics and ensures that every visible element on the dashboard is contextually valid for the selected vaccine.

---

## 8. Discussion {#discussion}

### 8.1 Data Quality Findings

The DQA results reveal systemic data quality challenges in Nepal's DHIS2 immunization reporting that have direct implications for policy and program management:

**Coverage Denominator Problem:** The 728 instances of coverage exceeding 100% are unlikely to represent genuine data entry errors by individual facilities. The pattern is consistent and widespread across both vaccines and time periods. The most plausible explanation is that the Surviving Infants denominator used in DHIS2 is significantly understated for Kavrepalanchok district, possibly because the denominator is based on census projections that do not capture actual catchment populations in peri-urban areas where facilities may serve populations from neighbouring districts. This finding has direct relevance to Nepal's national coverage reporting to WHO and UNICEF, both of which use DHIS2 data.

**Year-Boundary Consistency Violations:** The concentration of 255 drop-out logic violations in Shrawan (34) and Asar (35) — the first and last months of the Nepali fiscal year — strongly suggests an administrative reporting artefact rather than a genuine clinical phenomenon. This pattern is common in HMIS systems where facilities submit year-end adjustment reports that aggregate or re-balance cumulative counts, causing them to violate month-level drop-out rules.

**TCV Introduction Pattern:** The 20 missing TCV records correspond to periods before TCV was included in Nepal's national immunization schedule for Kavrepalanchok. The gradual transition from missing data to reported counts in the TCV column provides a natural experiment in how vaccine introduction events appear in aggregate HMIS data.

### 8.2 FHIR Standardization Outcomes

The 100% validation rate across all 1,098 generated FHIR resources demonstrates that programmatic FHIR generation using the `fhir.resources` library with Pydantic validation is a reliable approach for bulk DHIS2 data transformation. The two-level validation (structural + logical) provides confidence that the generated resources would be accepted by any conformant FHIR server.

The custom `nepali-fiscal-period` extension successfully resolves the calendar localization challenge without introducing any ambiguity in the ISO-8601 representation used for standard FHIR queries. This pattern could be adopted by any HMIS-to-FHIR pipeline dealing with non-Gregorian calendar systems.

### 8.3 Interoperability Demonstration

The FastAPI reference server and Streamlit dashboard together constitute a working proof-of-concept of the entire interoperability stack. The fact that the dashboard derives all its epidemiological insights — coverage trends, dropout rates, DQA findings, and longitudinal retention analysis — exclusively from FHIR JSON resources (via HTTP) confirms that FHIR standardization does not reduce the analytical utility of the data. On the contrary, the structured nature of FHIR enables richer queries and more reliable data parsing compared to flat CSV files.

The Dropout & Retention Analysis module is a particularly strong demonstration of this point. By computing the longitudinal dropout rate between Dose 1 and the final dose of each multi-dose vaccine family directly from parsed FHIR `MeasureReport` populations — with no recourse to the original DHIS2 CSV — it proves that the FHIR resources carry sufficient clinical granularity to support program-level retention monitoring. The system-wide dropout KPI on the landing page further allows programme managers to instantly identify which vaccine families have the highest dropout burden before drilling into any specific vaccine or fiscal year.

### 8.4 Limitations

1. **Single-district scope:** The dataset covers only Kavrepalanchok district. National-scale validation would require replication across all 77 districts, which may surface additional data quality patterns unique to different geographic and administrative contexts.

2. **Gregorian proxy dates:** The ISO-8601 dates assigned to `MeasureReport.period` are approximate conversions of Bikram Sambat months to Gregorian dates. These approximations (accurate to within ±1 day per month boundary) are sufficient for timeline charting but would not meet the precision requirements of a formal epidemiological date analysis.

3. **No patient-level linkage:** Because the source data is aggregate, it is not possible to link vaccination records to individual patients or to calculate more nuanced epidemiological metrics (e.g., dropout rates among specific age cohorts or geographic sub-populations within the district).

4. **Static data snapshot:** The pipeline processes a historical dataset. A production deployment would require integration with DHIS2's live API to process new monthly data automatically as it is reported.

---

## 9. Conclusion and Future Work {#conclusion}

### 9.1 Conclusion

This project successfully designed, implemented, and validated an end-to-end pipeline for converting Nepal's DHIS2 immunization aggregate data to HL7 FHIR R4 standards. The pipeline demonstrates:

1. **Comprehensive DQA capability:** The automated engine detected 728 coverage anomalies, 255 consistency violations, and formally validated 4,520 schema rule violations — establishing a quantitative evidence base for data quality improvement in Nepal's HMIS.

2. **FHIR compliance at scale:** 1,080 MeasureReport and 18 Measure resources were generated and achieved 100% structural and logical validation against the HL7 R4 specification.

3. **Clinical fidelity through FHIR extensions:** The custom `nepali-fiscal-period` extension and `DataAbsentReason` handling preserve the semantic richness of the Nepali health reporting context without loss of FHIR compliance.

4. **Formal standards specification:** The published FHIR Implementation Guide provides an internationally accessible, formally compiled specification of the Nepal Immunization Measure Reporting architecture, making it reproducible and auditable.

5. **Operational interoperability:** The FastAPI reference server and Streamlit dashboard demonstrate that FHIR-standardized data can directly power clinical decision-support applications with no intermediate data transformation step.

### 9.2 Future Work

1. **National scale-up:** Extend the pipeline to cover all 77 districts of Nepal by integrating with DHIS2's REST API for automated data extraction, enabling national-level coverage analysis.

2. **FHIR server deployment:** Deploy the reference API on a cloud platform (e.g., AWS, Azure) with a proper FHIR server (e.g., HAPI FHIR) to support multi-user access, versioning, and FHIR search operations.

3. **Predictive analytics integration:** Incorporate time-series forecasting models (e.g., ARIMA, Prophet) into the dashboard to predict future coverage shortfalls and trigger proactive supply chain alerts.

4. **Two-way DHIS2 integration:** Develop a feedback mechanism that writes DQA findings back into DHIS2 as validation alerts, enabling real-time data quality improvement at the facility level.

5. **Multi-district comparative analysis:** Extend the FHIR IG to support multi-district MeasureReports, enabling provincial and national comparative coverage dashboards.

---

## 10. References {#references}

1. HL7 International. (2019). *HL7 FHIR Release 4 — Measure Resource*. Retrieved from https://hl7.org/fhir/R4/measure.html

2. HL7 International. (2019). *HL7 FHIR Release 4 — MeasureReport Resource*. Retrieved from https://hl7.org/fhir/R4/measurereport.html

3. HL7 International. (2019). *HL7 FHIR Release 4 — DataAbsentReason Extension*. Retrieved from https://hl7.org/fhir/R4/extension-data-absent-reason.html

4. University of Oslo, HISP Centre. (2023). *DHIS2 Documentation*. Retrieved from https://docs.dhis2.org/

5. World Health Organization. (2017). *Data Quality Review: A Toolkit for Facility Data Quality Assessment*. WHO Document WHO/HIS/SDS/2017.23.

6. Ministry of Health and Population, Nepal. (2023). *National Immunization Program Annual Report*. Government of Nepal.

7. FHIR Shorthand (FSH) Documentation. (2023). *SUSHI User Guide*. Retrieved from https://fshschool.org/

8. Bosio, G., Reggi, L., & Casalini, M. (2022). *Leveraging FHIR for National Health Information Exchange: Lessons from Implementation*. Journal of Medical Internet Research, 24(4).

9. Shakya, P., Bhusal, C. K., & Karmacharya, B. M. (2021). *Assessment of immunization data quality in DHIS2: A case study from Nepal*. Health Informatics Journal, 27(2).

10. HL7 International. (2023). *IG Publisher Documentation*. Retrieved from https://confluence.hl7.org/display/FHIR/IG+Publisher+Documentation

---

## 11. Appendices {#appendices}

### Appendix A: Data Dictionary

| Column | Description | Type | Missing |
|---|---|---|---|
| SN | Serial Number (row identifier) | int64 | 0 |
| Fiscal Year | Nepali fiscal year (e.g., "2077/78") | str | 0 |
| Month No. | Nepali month number (1–12) | int64 | 0 |
| Month (EN) | English month name (e.g., "Shrawan") | str | 0 |
| Month (NP) | Nepali Devanagari month name | str | 0 |
| District | District name | str | 0 |
| Province | Province name | str | 0 |
| Dist. Code | District code | int64 | 0 |
| BCG through MR 2nd | Vaccine dose counts (17 columns) | int64 | 0 each |
| TCV (Col 19) | TCV dose count | float64 | 20 |
| Surviving Infants (Annual) | Annual target population | int64 | 0 |
| Surviving Infants (Monthly) | Monthly target population (denominator) | int64 | 0 |
| Facilities Expected | Health facilities expected to report | int64 | 0 |
| Facilities Reported | Health facilities that reported | float64 | 7 |
| Facilities Not Reported | Health facilities that did not report | float64 | 7 |

### Appendix B: FHIR Validation Summary

```
==================================================
FHIR VALIDATION REPORT
==================================================
MEASURE RESOURCES
--------------------------------------------------
Total Measure Resources Audited: 18
Structurally Valid: 18/18
Status: PASS

MEASUREREPORT DATA VALIDATION
--------------------------------------------------
Total MeasureReport Resources Audited: 1080
Structurally Valid (FHIR R4 Schema): 1080/1080
Logically Consistent (Math & Extensions): 1080/1080
Status: PASS
==================================================
```

### Appendix C: FHIR MeasureReport Sample (fIPV1, Shrawan 2077/78)

```json
{
  "resourceType": "MeasureReport",
  "id": "measure-fipv1-row-1",
  "extension": [
    {
      "extension": [
        { "url": "fiscalYear", "valueString": "2077/78" },
        { "url": "monthEnglish", "valueString": "Shrawan" },
        { "url": "monthNepali", "valueString": "श्रावण" },
        { "url": "district", "valueString": "Kavrepalanchok" }
      ],
      "url": "http://example.org/fhir/StructureDefinition/nepali-fiscal-period"
    }
  ],
  "status": "complete",
  "type": "summary",
  "measure": "http://example.org/fhir/Measure/measure-fipv1",
  "period": {
    "start": "2020-07-16T00:00:00Z",
    "end": "2020-08-15T23:59:59Z"
  },
  "group": [
    {
      "population": [
        {
          "code": { "coding": [{ "system": "...", "code": "initial-population" }] },
          "count": 448
        },
        {
          "code": { "coding": [{ "system": "...", "code": "denominator" }] },
          "count": 448
        },
        {
          "code": { "coding": [{ "system": "...", "code": "numerator" }] },
          "count": 498
        }
      ],
      "measureScoreQuantity": { "value": 111.16, "unit": "%" }
    }
  ]
}
```

### Appendix D: API Endpoint Reference

| Endpoint | Method | Response | Description |
|---|---|---|---|
| `/` | GET | JSON | Health check |
| `/fhir/Measure` | GET | FHIR Bundle | All 18 Measure blueprints |
| `/fhir/Measure/{id}` | GET | FHIR Measure | Single Measure (e.g., `measure-bcg`) |
| `/fhir/MeasureReport` | GET | FHIR Bundle | All 1,080 MeasureReports |
| `/fhir/MeasureReport/{id}` | GET | FHIR MeasureReport | Single MeasureReport (e.g., `measure-bcg-row-1`) |

### Appendix E: Published FHIR Implementation Guide

**URL:** [https://saurav8989.github.io/Project/](https://saurav8989.github.io/Project/)

The published IG includes:
- StructureDefinition for `NepalImmunizationMeasure` profile
- StructureDefinition for `NepalImmunizationMeasureReport` profile
- Extension definition for `nepali-fiscal-period`
- CodeSystem: `VaccineIndicators` (18 codes)
- ValueSet: `VaccineIndicatorsVS`
- Machine-readable JSON StructureDefinition artifacts
- Human-readable narrative pages

---

*Submitted in partial fulfillment of the requirements for the degree of Master of Health Informatics*  
*May 2026*