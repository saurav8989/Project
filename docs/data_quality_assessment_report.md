# DHIS2 Immunization Data Quality Assessment (DQA) Report

**Date:** May 2026  
**Dataset:** `Data.xlsx` (5 Years Monthly Data, 60 records)  
**Scope:** Evaluation of data completeness, internal logical consistency, and statistical plausibility for DHIS2 immunization records.

---

## Executive Summary
A comprehensive Data Quality Assessment was conducted on the 5-year immunization dataset. While the structural integrity of the dataset is sound, significant data quality issues were identified within the reported metrics. Specifically, massive over-reporting leading to >100% coverage rates and 255 logical drop-out violations indicate that the raw data requires significant cleaning and contextual validation before it can be reliably mapped to FHIR resources or used for clinical decision-making.

---

## A. Completeness Assessment

The completeness assessment evaluated both facility reporting rates and vaccine-specific indicator missingness.

### 1. Reporting Completeness
Reporting Completeness = `(Facilities Reporting / 161) * 100`

- **Overall Trend:** Facility reporting has shown a steady and positive improvement over the 5-year period.
  - FY 2077/78: **75.21%**
  - FY 2078/79: **75.91%**
  - FY 2079/80: **86.33%**
  - FY 2080/81: **87.91%**
  - FY 2081/82: **87.80%**
- **Monthly Seasonality:** Reporting peaks in Baishak (88.35%) and experiences a significant dip in Poush (75.16%).

### 2. Indicator Completeness
Indicator Completeness = `(Non-missing Values / Total Expected Values) * 100`

- **Core Vaccines:** 100% complete. All standard vaccines (BCG, Rota, OPV, fIPV, PCV, Penta, MR, JE) contain zero missing values across the entire 5-year span.
- **Exceptions:** `TCV` (Typhoid Conjugate Vaccine) is only **66.67% complete** (20 missing records).

---

## B. Internal Consistency Checks

Internal consistency evaluates whether the data follows expected logical rules, specifically focusing on multi-dose vaccine drop-out rules (e.g., Dose 1 should always be $\ge$ Dose 2).

### Findings
⚠️ **255 Total Rule Violations Detected**
The dataset contains 255 instances where a subsequent dose count was impossibly higher than a prior dose count.

**Most Frequently Violated Rules:**
1. `MR1 >= MR2`: 34 violations
2. `Penta2 >= Penta3`: 32 violations
3. `OPV2 >= OPV3`: 31 violations
4. `PCV2 >= PCV3`: 30 violations

**Temporal Trend:**
Violations are heavily concentrated around the transition of the Nepali fiscal year, spiking in **Asar** (35 violations) and **Shrawan** (34 violations). This suggests administrative reporting errors during year-end/year-start reporting rather than isolated clinical anomalies.

---

## C. Plausibility & Outlier Detection

Plausibility checks utilized coverage formulas and advanced statistical algorithms (Z-Score & IQR) to detect highly improbable data points.

### 1. Impossible Coverage Anomalies
Coverage = `(Vaccinated Children / Surviving Infants (Monthly)) * 100`

⚠️ **728 instances of >100% Coverage Detected**
Over a thousand data points claim that more children were vaccinated than actually exist in the target population. 
- *Example:* BCG coverage reached an impossible 185.9% in Ashwin 2077/78.
- *Conclusion:* This indicates either systemic over-reporting by facilities (e.g., counting out-of-district children) or a deeply flawed/underestimated target population denominator.

### 2. Statistical Outliers (Spikes and Drops)
Using Z-score ($|z| > 3$) and IQR bounding algorithms on the raw dose counts, the system flagged **20 extreme statistical outliers**:
- **13 Sudden Spikes** (unexplainable surges in vaccine administration)
- **7 Abnormal Drops** (unexplainable collapses in vaccine administration)

These statistical outliers exist independently of the population denominator and point to pure data-entry errors or localized reporting failures.

---

## Recommendations for Phase 4 (Data Cleaning)
1. **Handle Missing TCV Data:** Interpolate or drop the 20 missing `NaN` values in the TCV column.
2. **Resolve Consistency Violations:** Apply logic to smooth or drop the 255 records where Dose 2 > Dose 1.
3. **Address Denominator Issues:** Determine if coverage caps at 100% should be enforced mathematically, or if the raw counts should be mapped "as-is" to FHIR regardless of the population denominator.
