CodeSystem: NepalVaccineIndicatorCS
Id: nepal-vaccine-indicator-cs
Title: "Nepal DHIS2 Vaccine Indicator Code System"
Description: "Specific vaccine dose indicators used in Nepal's DHIS2 immunization registry."
* ^caseSensitive = true
* #BCG "BCG Dose" "BCG (Tuberculosis) vaccine"
* #Rota_1 "Rota 1st Dose" "Rotavirus vaccine 1st Dose"
* #Rota_2 "Rota 2nd Dose" "Rotavirus vaccine 2nd Dose"
* #OPV_1 "OPV 1st Dose" "Oral Polio Vaccine 1st Dose"
* #OPV_2 "OPV 2nd Dose" "Oral Polio Vaccine 2nd Dose"
* #OPV_3 "OPV 3rd Dose" "Oral Polio Vaccine 3rd Dose"
* #fIPV_1 "fIPV 1st Dose" "Fractional Inactivated Polio Vaccine 1st Dose"
* #fIPV_2 "fIPV 2nd Dose" "Fractional Inactivated Polio Vaccine 2nd Dose"
* #PCV_1 "PCV 1st Dose" "Pneumococcal Conjugate Vaccine 1st Dose"
* #PCV_2 "PCV 2nd Dose" "Pneumococcal Conjugate Vaccine 2nd Dose"
* #PCV_3 "PCV 3rd Dose" "Pneumococcal Conjugate Vaccine 3rd Dose"
* #Penta_1 "Penta 1st Dose" "Pentavalent vaccine 1st Dose"
* #Penta_2 "Penta 2nd Dose" "Pentavalent vaccine 2nd Dose"
* #Penta_3 "Penta 3rd Dose" "Pentavalent vaccine 3rd Dose"
* #MR_1 "MR 1st Dose" "Measles Rubella vaccine 1st Dose"
* #MR_2 "MR 2nd Dose" "Measles Rubella vaccine 2nd Dose"
* #JE "JE Dose" "Japanese Encephalitis vaccine"
* #TCV "TCV Dose" "Typhoid Conjugate Vaccine"

ValueSet: NepalVaccineIndicatorVS
Id: nepal-vaccine-indicator-vs
Title: "Nepal DHIS2 Vaccine Indicator Value Set"
Description: "Value set containing all 18 Nepal-specific vaccine dose indicators."
* include codes from system NepalVaccineIndicatorCS
