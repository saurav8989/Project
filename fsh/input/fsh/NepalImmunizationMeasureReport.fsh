Profile: NepalImmunizationMeasureReport
Parent: MeasureReport
Id: nepal-immunization-measure-report
Title: "Nepal DHIS2 Immunization MeasureReport"
Description: "A strict profile on the MeasureReport resource to enforce constraints for Nepal's aggregate DHIS2 immunization reporting."

// Enforce that this report must link to our custom Measure definition
* measure ^type[0].targetProfile = "http://mohp.gov.np/fhir/StructureDefinition/nepal-immunization-measure"

// Enforce that this is a summary report (aggregate data), not an individual patient report
* type = #summary

// Enforce the Geography Rule: It must be for a Geographic Location (District or Facility)
* subject 1..1
* subject only Reference(Location)

// Enforce the Period and the custom DHIS2 Nepali calendar extension
* period 1..1
* period.extension contains NepaliFiscalPeriod named nepaliFiscalPeriod 1..1

// Enforce the Facility Reporting Status extension at the root
* extension contains FacilityReportingStatus named facilityReportingStatus 1..1

// Enforce that the reported populations map to the Numerator and Denominator
* group 1..*
* group.population ^slicing.discriminator.type = #value
* group.population ^slicing.discriminator.path = "code.coding.code"
* group.population ^slicing.rules = #open
* group.population contains
    numerator 1..1 and
    denominator 1..1

* group.population[numerator].code = http://terminology.hl7.org/CodeSystem/measure-population#numerator
* group.population[denominator].code = http://terminology.hl7.org/CodeSystem/measure-population#denominator
