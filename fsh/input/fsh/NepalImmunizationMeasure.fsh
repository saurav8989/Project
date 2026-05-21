Profile: NepalImmunizationMeasure
Parent: Measure
Id: nepal-immunization-measure
Title: "Nepal DHIS2 Immunization Measure"
Description: "A strict profile on the Measure resource to define public health immunization indicators in Nepal."

// Enforce that this is a proportion measure (Numerator / Denominator)
* scoring = http://terminology.hl7.org/CodeSystem/measure-scoring#proportion

// Enforce that the measure topic comes from our custom Vaccine Vocabulary
* topic from nepal-vaccine-indicator-vs (extensible)

// Enforce that there must be exactly one Numerator and exactly one Denominator
* group 1..*
* group.population ^slicing.discriminator.type = #value
* group.population ^slicing.discriminator.path = "code.coding.code"
* group.population ^slicing.rules = #open
* group.population contains
    numerator 1..1 and
    denominator 1..1

* group.population[numerator].code = http://terminology.hl7.org/CodeSystem/measure-population#numerator
* group.population[denominator].code = http://terminology.hl7.org/CodeSystem/measure-population#denominator
