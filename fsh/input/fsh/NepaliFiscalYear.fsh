Extension: NepaliFiscalPeriod
Id: nepali-fiscal-period
Title: "Nepali Fiscal Period"
Description: "An extension to capture the original Bikram Sambat (Nepali) fiscal year and month string exactly as extracted from DHIS2."
* ^context[0].type = #element
* ^context[0].expression = "MeasureReport.period"
* value[x] only string
