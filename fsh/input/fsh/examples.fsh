// ==============================================================================
// FHIR Instances for the Implementation Guide
// These examples demonstrate how real-world data is structured using the profiles.
// ==============================================================================

// ------------------------------------------------------------------------------
// Example 1: The Geographic Location
// ------------------------------------------------------------------------------
Instance: loc-kavrepalanchok
InstanceOf: Location
Title: "Location Example: Kavrepalanchok District"
Description: "An example of a geographic location (District level) in Nepal."
Usage: #example
* status = #active
* name = "Kavrepalanchok District, Nepal"
* physicalType = http://terminology.hl7.org/CodeSystem/location-physical-type#jdn "Jurisdiction"

// ------------------------------------------------------------------------------
// Example 2: The Reporting Organization
// ------------------------------------------------------------------------------
Instance: org-dho-kavre
InstanceOf: Organization
Title: "Organization Example: DHO Kavrepalanchok"
Description: "An example of a District Health Office in Nepal."
Usage: #example
* active = true
* name = "District Health Office, Kavrepalanchok"
* alias[0] = "DHO Kavre"

// ------------------------------------------------------------------------------
// Example 3: The MeasureReport (Payload)
// ------------------------------------------------------------------------------
Instance: measurereport-penta1-example
InstanceOf: NepalImmunizationMeasureReport
Title: "MeasureReport Example: Penta 1 Coverage for Shrawan 2077"
Description: "A complete example of a monthly aggregate coverage report conforming to the Nepal Immunization MeasureReport profile."
Usage: #example
* status = #complete
* type = #summary

// Link to the custom Measure (e.g., Penta 1 Indicator)
* measure = "http://mohp.gov.np/fhir/Measure/measure-penta1"

// External References to Subject and Reporter
* subject = Reference(loc-kavrepalanchok)
* reporter = Reference(org-dho-kavre)

// The proxy Gregorian period for standard FHIR dashboard plotting
* period.start = "2020-07-16T00:00:00Z"
* period.end = "2020-08-15T23:59:59Z"

// The custom Nepali calendar extension
* period.extension[nepaliFiscalPeriod].extension[fiscalYear].valueString = "2077/78"
* period.extension[nepaliFiscalPeriod].extension[monthEnglish].valueString = "Shrawan"
* period.extension[nepaliFiscalPeriod].extension[monthNepali].valueString = "साउन"
* period.extension[nepaliFiscalPeriod].extension[district].valueString = "Kavrepalanchok"

// The Facility Reporting Status extension at the root
* extension[facilityReportingStatus].extension[expected].valueInteger = 161
* extension[facilityReportingStatus].extension[reported].valueInteger = 139
* extension[facilityReportingStatus].extension[notReported].valueInteger = 22

// The Group containing the population data
* group[0].population[numerator].code = http://terminology.hl7.org/CodeSystem/measure-population#numerator
* group[0].population[numerator].count = 540

* group[0].population[denominator].code = http://terminology.hl7.org/CodeSystem/measure-population#denominator
* group[0].population[denominator].count = 600

// Measure Score (Coverage Percentage)
* group[0].measureScore.value = 90.0
* group[0].measureScore.unit = "%"
* group[0].measureScore.system = "http://unitsofmeasure.org"
* group[0].measureScore.code = #%
