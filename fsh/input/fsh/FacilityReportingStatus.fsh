// ==============================================================================
// Custom Extension: Facility Reporting Status
// ==============================================================================

Extension: FacilityReportingStatus
Id: facility-reporting-status
Title: "Facility Reporting Status"
Description: "An extension to capture the administrative reporting metadata (completeness) of health facilities contributing to an aggregate MeasureReport."

// This extension is attached to the root of the MeasureReport
* ^context[0].type = #element
* ^context[0].expression = "MeasureReport"

// Define the three sub-extensions
* extension contains
    expected 1..1 and
    reported 1..1 and
    notReported 1..1

// Constrain all sub-extensions to be integers
* extension[expected].value[x] only integer
* extension[expected].valueInteger ^short = "Total number of health facilities expected to report"

* extension[reported].value[x] only integer
* extension[reported].valueInteger ^short = "Number of health facilities that successfully reported"

* extension[notReported].value[x] only integer
* extension[notReported].valueInteger ^short = "Number of health facilities that failed to report"
