Extension: NepaliFiscalPeriod
Id: nepali-fiscal-period
Title: "Nepali Fiscal Period"
Description: "An extension to capture the original Bikram Sambat (Nepali) fiscal year and month string exactly as extracted from DHIS2."
* ^context[0].type = #element
* ^context[0].expression = "MeasureReport.period"
* extension contains
    fiscalYear 1..1 and
    monthEnglish 1..1 and
    monthNepali 1..1 and
    district 1..1

* extension[fiscalYear].value[x] only string
* extension[monthEnglish].value[x] only string
* extension[monthNepali].value[x] only string
* extension[district].value[x] only string
