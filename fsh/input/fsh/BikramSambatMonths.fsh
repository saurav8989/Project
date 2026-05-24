// ==============================================================================
// CodeSystem and ValueSet for Bikram Sambat Months
// ==============================================================================

CodeSystem: BikramSambatMonthsCS
Id: bs-months-cs
Title: "Bikram Sambat Months CodeSystem"
Description: "The 12 months of the Bikram Sambat (Nepali) calendar, using standardized DHIS2 English spellings as the codes."
* #Baisakh "Baisakh (वैशाख)"
* #Jestha "Jestha (जेठ)"
* #Ashadh "Ashadh (असार)"
* #Shrawan "Shrawan (साउन)"
* #Bhadra "Bhadra (भदौ)"
* #Ashwin "Ashwin (असोज)"
* #Kartik "Kartik (कात्तिक)"
* #Mangsir "Mangsir (मंसिर)"
* #Poush "Poush (पुष)"
* #Magh "Magh (माघ)"
* #Falgun "Falgun (फागुन)"
* #Chaitra "Chaitra (चैत)"

ValueSet: BikramSambatMonthsVS
Id: bs-months-vs
Title: "Bikram Sambat Months ValueSet"
Description: "ValueSet containing the English spelling of the 12 Bikram Sambat months, used to strictly validate DHIS2 extract strings."
* include codes from system BikramSambatMonthsCS
