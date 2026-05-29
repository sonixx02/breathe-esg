# TRADEOFFS.md

# Things I deliberately did not build
## 1. I did not build live external APIs

I did not connect to:

- SAP OData
- SAP BAPI
- SAP IDoc pipeline
- Concur API
- Navan API
- Utility API


What I built instead:

CSV upload with realistic fields.

Example:

```text
SAP admin exports fuel purchases
Analyst uploads CSV
System normalizes rows
Analyst reviews results
```

What production would add:

- scheduled API pulls
- connector health checks
- retry logic
- credential storage
- source-specific error monitoring

## 2. I did not build PDF or XML utility parsing

I only support utility CSV.

Why I skipped it:

PDF bills are hard to parse reliably because every utility bill looks different. Green Button XML is useful, but it adds schema work that is not needed to prove the main workflow.

What I built instead:

A utility CSV parser that handles:

- meter ID
- site
- billing period
- usage
- unit
- tariff
- cost

Example:

```text
MTR-001, Mumbai HQ, 2024-01-15, 2024-02-14, 48200, kWh
```

What production would add:

- Green Button XML parser
- interval readings
- PDF extraction
- calendar-month proration
- more utility-specific fields

## 3. I did not build a full carbon calculation engine

The app does not calculate final CO2e totals.


What I built instead:

I normalize activity data and assign scope/category.

Example:

```text
DIESEL-HSD -> Scope 1, Mobile Combustion
48200 kWh electricity -> Scope 2, Purchased Electricity
BOM to LHR flight -> Scope 3, Flight - Economy
```

What production would add:

- emission factor tables
- country-specific grid factors
- fuel-specific factors
- factor version history
- calculated CO2e totals

## 4. i did not handle all types of languages conversion or handled different type of values ex: currency format , etc only showed simple things for demo prposes that i thought abt it 

