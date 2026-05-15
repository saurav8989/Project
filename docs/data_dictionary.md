# DHIS2 Immunization Data Dictionary

This document outlines the structure of the `Data.xlsx` dataset extracted from DHIS2 for the project.

| Column | Description | Type |
| :--- | :--- | :--- |
| **SN** | Serial Number / unique identifier for the row | Integer (`int64`) |
| **Fiscal Year** | The Nepali fiscal year of the report (e.g., "2077/78") | String (`object`) |
| **Month No.** | The numerical representation of the month in the Nepali calendar (1-12) | Integer (`int64`) |
| **Month (EN)** | The English transliteration of the Nepali month (e.g., "Shrawan") | String (`object`) |
| **Month (NP)** | The Nepali script representation of the month (e.g., "श्रावण") | String (`object`) |
| **District** | The name of the district where data was collected (e.g., "Kavrepalanchok") | String (`object`) |
| **Province** | The name of the province the district belongs to (e.g., "Bagmati") | String (`object`) |
| **Dist. Code** | Standardized numerical code assigned to the district | Integer (`int64`) |
| **BCG (Col 2)** | Total doses administered for the BCG (Tuberculosis) vaccine | Integer (`int64`) |
| **Rota 1st (Col 3)** | Total 1st doses administered for the Rotavirus vaccine | Integer (`int64`) |
| **Rota 2nd (Col 4)** | Total 2nd doses administered for the Rotavirus vaccine | Integer (`int64`) |
| **OPV 1st (Col 5)** | Total 1st doses administered for the Oral Polio Vaccine | Integer (`int64`) |
| **OPV 2nd (Col 6)** | Total 2nd doses administered for the Oral Polio Vaccine | Integer (`int64`) |
| **OPV 3rd (Col 7)** | Total 3rd doses administered for the Oral Polio Vaccine | Integer (`int64`) |
| **fIPV 1st (Col 8)** | Total 1st doses administered for Fractional Inactivated Polio Vaccine | Integer (`int64`) |
| **fIPV 2nd (Col 9)** | Total 2nd doses administered for Fractional Inactivated Polio Vaccine | Integer (`int64`) |
| **PCV 1st (Col 10)** | Total 1st doses administered for Pneumococcal Conjugate Vaccine | Integer (`int64`) |
| **PCV 2nd (Col 11)** | Total 2nd doses administered for Pneumococcal Conjugate Vaccine | Integer (`int64`) |
| **PCV 3rd (Col 12)** | Total 3rd doses administered for Pneumococcal Conjugate Vaccine | Integer (`int64`) |
| **Penta 1st (Col 13)** | Total 1st doses administered for Pentavalent vaccine (DTP-HepB-Hib) | Integer (`int64`) |
| **Penta 2nd (Col 14)** | Total 2nd doses administered for Pentavalent vaccine | Integer (`int64`) |
| **Penta 3rd (Col 15)** | Total 3rd doses administered for Pentavalent vaccine | Integer (`int64`) |
| **MR 1st (Col 16)** | Total 1st doses administered for Measles & Rubella vaccine | Integer (`int64`) |
| **MR 2nd (Col 17)** | Total 2nd doses administered for Measles & Rubella vaccine | Integer (`int64`) |
| **JE (Col 18)** | Total doses administered for Japanese Encephalitis vaccine | Integer (`int64`) |
| **TCV (Col 19)** | Total doses administered for Typhoid Conjugate Vaccine | Float (`float64`)* |
| **Surviving Infants (Annual)** | Estimated annual target population of surviving infants in the district | Integer (`int64`) |
| **Surviving Infants (Monthly)** | Estimated monthly target population of surviving infants in the district | Integer (`int64`) |
| **Facilities Expected** | Total number of health facilities expected to submit a report this month | Integer (`int64`) |
| **Facilities Reported** | Total number of health facilities that successfully submitted a report | Float (`float64`)* |
| **Facilities Not Reported**| Total number of health facilities that failed to submit a report | Float (`float64`)* |

*\*Note: TCV, Facilities Reported, and Facilities Not Reported are loaded as `float64` purely due to the presence of missing (NaN) values in the raw dataset. They represent whole integers conceptually.*
