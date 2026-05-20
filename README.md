# 🏥 National Childhood Immunization Analytics & DQA (FHIR Interoperability)

**Master's Thesis in Health Informatics**

This repository contains the complete engineering pipeline for standardizing, validating, and visualizing 5 years (60 months) of DHIS2 aggregate public health data into HL7 FHIR (R4) standards. It demonstrates how to achieve strict clinical interoperability while preserving rigorous Data Quality Assessment (DQA) metadata.

---

## 🎯 Core Objectives

1. **Data Quality Assessment (DQA):** Programmatically audit raw DHIS2 aggregate data to detect logical drop-out violations, mathematical coverage anomalies (>100%), and missing records across 18 vaccine indicators.
2. **FHIR Standardization:** Engineer a Python-based ETL pipeline to transform raw statistical datasets into standardized, strictly-validated HL7 FHIR `Measure` and `MeasureReport` JSON payloads.
3. **Interoperability & Analytics:** Prove the real-world utility of standardizing data by exposing the FHIR resources via a custom `FastAPI` Reference Server and consuming them in a dynamic, interactive `Streamlit` clinical decision-support dashboard.

---

## 🏗️ Architecture & Pipeline

The project follows a linear, 8-phase engineering pipeline:

1. **`DHIS2 (CSV)`** ➔ Raw data ingestion and profiling (Handling missing data, standardizing columns).
2. **`Data Cleaning`** ➔ Python `pandas` engineering resulting in a pristine dataset.
3. **`FHIR JSON Generation`** ➔ Mapping DHIS2 aggregate counts to FHIR `MeasureReport` populations (Numerator, Denominator) and utilizing `DataAbsentReason` extensions for clinical fidelity.
4. **`Validation Engine`** ➔ Automated structural and logical audits using `fhir.resources` and Pydantic.
5. **`FastAPI Server`** ➔ A custom REST API (`http://127.0.0.1:8000/fhir`) serving the validated resources.
6. **`Streamlit Analytics UI`** ➔ A real-time web dashboard that consumes the API to render interactive epidemiological trends and DQA audits.

---

## 📁 Repository Structure

```text
Project/
├── data/
│   ├── raw/                 # Original DHIS2 extracts
│   ├── processed/           # Cleaned_Data.csv (Post-ETL)
│   └── fhir/                # 1,098 generated FHIR JSON payloads
├── docs/                    # Architectural mappings and Data Dictionaries
├── outputs/                 
│   ├── figures/             # High-res academic publication plots (Boxplots, Heatmaps, etc.)
│   └── *.txt, *.md          # Automated validation and progress reports
└── scripts/
    ├── data_cleaning/       # Phase 2: Standardization scripts
    ├── quality_assessment/  # Phase 3: DQA constraint checks and statistical outlier logic
    ├── fhir_mapping/        # Phase 5: Python generators for Measure and MeasureReport
    ├── validation/          # Phase 6: FHIR Schema auditing algorithms
    ├── visualization/       # Academic plot generation (matplotlib/seaborn)
    └── api/                 # Phase 7 & 8: FastAPI Reference Server & Streamlit Dashboard
```

---

## 🚀 How to Run the Project Locally

### 1. Environment Setup
Ensure you have Python 3.9+ installed. Clone the repository and install the dependencies:
```bash
git clone <your-repo-url>
cd Project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch the FHIR Reference API
Start the backend server to host the generated FHIR JSON files.
```bash
./venv/bin/python scripts/api/fhir_server.py
```
*The API will be live at `http://127.0.0.1:8000`. You can view the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.*

### 3. Launch the Clinical Analytics Dashboard
In a **new terminal window**, activate the environment and start the Streamlit UI:
```bash
source venv/bin/activate
./venv/bin/python -m streamlit run scripts/api/dashboard.py
```
*The dashboard will automatically open in your default web browser.*

---

## 📊 Key Findings & Validation Highlights

* **100% FHIR Compliance:** Successfully generated and audited 1,080 distinct `MeasureReport` resources and 18 `Measure` blueprints. Every single resource passed strict HL7 FHIR (R4) Structural Schema Validation.
* **Mathematical Integrity:** Achieved 100% logical consistency; the recalculated `(Numerator / Denominator) * 100` algorithms matched the embedded FHIR `measureScoreQuantity` natively across all 5 years of data.
* **Clinical Fidelity Maintained:** Accurately utilized standard FHIR extensions (`http://hl7.org/fhir/StructureDefinition/data-absent-reason`) to handle missing real-world DHIS2 data (e.g., unreported TCV metrics) without destructive interpolation or breaking interoperability rules.
