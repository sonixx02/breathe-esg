# SOURCES.md

# Source research and sample data

## 1. SAP fuel and procurement

What I looked at:

- SAP purchase order item fields
- SAP units of measure
- SAP IDoc structure

Useful references:

- https://help.sap.com/docs/SAP_S4HANA_CLOUD/bb9f1469daf04bd894ab2167f8132a1a/579e67f98b9c4ad29ea9bb89c2c1c664.html
- https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/af9ef57f504840d2b81be8667206d485/af7eb65334e6b54ce10000000a174cb4.html

What I learned:

SAP purchasing data usually has item-level fields like:

- purchase order
- material
- plant
- quantity
- unit
- date

SAP field names can be technical. For example:

```text
MATNR -> material code
WERKS -> plant
MENGE -> quantity
MEINS -> unit
```

Why I chose CSV:

SAP IDocs are realistic, but they are harder to parse because data sits inside segment payloads. For this prototype, CSV is a better first version because it is still realistic and easier to review.

What my sample SAP data includes:

```text
4500012891, DIESEL-HSD, PLT_101, 48000, L
```

This is a normal valid row.

```text
4500012894, DIESEL-HSD, PLT_999, 5000, L
```

This fails because the plant code is unknown.

```text
4500012896, PACKAGING-BOX, PLT_101, 500, PCS
```

This fails because packaging is not part of the fuel subset I chose.

What would break in a real deployment:

- client-specific SAP report columns
- more language/header variations
- more material codes
- more units
- duplicate exports
- difference between PO quantity, goods receipt quantity, and invoice quantity

## 2. Utility electricity

What I looked at:

- Oracle Green Button Download My Data docs
- Green Button Alliance docs

Useful references:

- https://docs.oracle.com/en/industries/utilities/digital-self-service/energy-management-overview/green-button-downloadmydata.html
- https://www.greenbuttonalliance.org/green-button-connect-my-data-cmd

What I learned:

Utility exports can include:

- billing periods
- usage
- units
- cost
- account or meter details
- interval readings in more advanced exports

The important issue is that billing periods do not always match calendar months.

Example:

```text
2024-01-15 to 2024-02-14
```

This cannot honestly be called only January or only February.

Why I chose CSV:

A facilities team can download a portal CSV. PDF parsing and XML parsing are real options, but they add extra complexity.

What my sample utility data includes:

```text
MTR-001, Mumbai HQ, 2024-01-15, 2024-02-14, 48200, kWh
```

This is a normal billing-period row.

```text
MTR-002, Pune Office, 2024-01-01, 2024-01-31, 12500000, Wh
```

This tests unit conversion from `Wh` to `kWh`.

```text
MTR-004, Delhi Warehouse, 2024-01-01, blank, 8500, kWh
```

This fails because the billing end date is missing.

What would break in a real deployment:

- interval data instead of billing data
- many meters per site
- utility-specific CSV headers
- missing tariff details
- demand charges
- need to split billing periods across months

## 3. Corporate travel

What I looked at:

- SAP Concur Air Carbon Footprint report docs
- SAP Concur travel emissions docs

Useful references:

- https://help.sap.com/docs/SAP_CONCUR/d314a525472c49548219b560516c9b8d/1c387aa9700b1014a46a108435d32877.html
- https://help.sap.com/docs/COMPLETE/3483c8abdb4a4176950eee0d672a7198/ea234a25cd064f5080f5ecd746b79fb7.html

What I learned:

Travel data can include:

- traveler
- travel date
- origin
- destination
- route distance
- class of service
- hotels
- ground transport

For flights, distance is not always directly available. Sometimes we only get airport codes.

Why I chose CSV:

Live Concur/Navan APIs need credentials and OAuth setup. A CSV export is enough for this assignment and still shows the real parsing issues.

What my sample travel data includes:

```text
flight, BOM, LHR, 7200, economy
```

This is a flight row with distance already present.

```text
flight, BOM, JFK, blank, business
```

This tests fallback distance calculation using airport coordinates.

```text
flight, BOM, XYZ, blank, economy
```

This fails because `XYZ` is not in the airport lookup table.

```text
hotel, London, 3 nights
```

This tests hotel rows, where the useful activity value is nights, not kilometers.

What would break in a real deployment:

- multi-leg flights
- layovers
- vendor-provided emissions values
- missing airport codes
- inconsistent cabin class names
- hotel country factors
- taxi trips with no distance

## Why these sample files are enough

Each source has:

- valid rows
- failed rows
- suspicious rows
- unit or lookup problems
- source-specific shape differences

That gives the analyst dashboard meaningful data to review without pretending this is a complete production ESG platform.
