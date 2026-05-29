# MODEL.md

# Data model

This app has one main idea: keep the original uploaded data, then create a cleaner record from it.

I did this because ESG data is audit-heavy. If a row fails or gets edited later, I still want to show what the client originally gave us.

The flow is:

```text
CSV upload
-> IngestionBatch
-> RawIngestionRow
-> parser
-> EmissionRecord
-> analyst review
-> approve
-> lock
```

## Client

`Client` is the company whose data we are handling.

For the demo, I seed one client: `Acme Corp`.

Why I added it:

- The assignment asks for multi-tenancy.
- Even if the demo has one company, the model should not mix one client's data with another client's data.

Example:

```text
Client: Acme Corp
```

All batches, raw rows, records, plant mappings, and material mappings belong to a client.

## IngestionBatch

`IngestionBatch` means one file upload.

Example:

```text
source_type: SAP
file_name: sample_sap.csv
uploaded_by: analyst
total_rows: 6
parsed_rows: 4
failed_rows: 2
flagged_rows: 2
```

Why I added it:

- I need to know which file produced which rows.
- It helps the dashboard show whether an upload worked or had errors.
- It gives a clean audit trail starting point.

## RawIngestionRow

`RawIngestionRow` stores the original row from the CSV as JSON.

Example raw SAP row:

```json
{
  "po_number": "4500012891",
  "material_code": "DIESEL-HSD",
  "plant_code": "PLT_101",
  "quantity": "48000",
  "unit": "L",
  "doc_date": "15.03.2024"
}
```

Why I added it:

- The original data should not disappear.
- Failed rows should still be visible.
- If an analyst edits the normalized record later, we can compare it to the original row.

If a row has an unknown plant code, I do not drop it. I keep it and mark it failed:

```text
parse_status: FAILED
parse_error: Unknown plant code: PLT_999
```

## EmissionRecord

`EmissionRecord` is the clean record that the analyst reviews.

Example normalized SAP row:

```text
source_type: SAP
scope: 1
activity_category: Mobile Combustion
raw_value: 48000
raw_unit: L
normalized_value: 48000
normalized_unit: L
location_raw: PLT_101
location_name: Mumbai Refinery
status: PENDING
```

Why I added it:

- SAP, utility, and travel files have different columns.
- The dashboard needs one common shape to show all records.
- Auditors need both original value and normalized value.

For utility data, an example normalized row is:

```text
source_type: UTILITY
scope: 2
activity_category: Purchased Electricity
period_start: 2024-01-15
period_end: 2024-02-14
normalized_value: 48200
normalized_unit: kWh
location_raw: MTR-001
location_name: Mumbai HQ
```

For travel data, an example normalized row is:

```text
source_type: TRAVEL
scope: 3
activity_category: Flight - Economy
normalized_value: 7200
normalized_unit: km
location_raw: BOM->LHR
location_name: BOM to LHR
```

## ActivityLog

`ActivityLog` records important changes.

Actions I track:

- `CREATED`
- `FLAGGED`
- `EDITED`
- `APPROVED`
- `LOCKED`

Example:

```text
record: 12
action_type: APPROVED
acted_by: analyst
comment: Checked against source row
```

Why I added it:

- The assignment asks for audit trail.
- If someone changes a value, I want old and new values saved.
- If someone approves or locks a row, I want the user and time saved.

## PlantMaster

`PlantMaster` maps SAP plant codes to readable names.

Example:

```text
PLT_101 -> Mumbai Refinery
PLT_102 -> Pune Plant
```

Why I added it:

SAP plant codes are not useful by themselves. An analyst should not have to know what `PLT_101` means.

## MaterialCategoryMap

`MaterialCategoryMap` maps SAP material codes to scope and activity category.

Example:

```text
DIESEL-HSD -> Scope 1, Mobile Combustion
LPG-CYL -> Scope 1, Stationary Combustion
```

Why I added it:

Scope should come from what the activity is, not only from the source system.

For example, both rows may come from SAP, but the material decides what kind of activity it is.

## AirportMaster

`AirportMaster` stores airport code and coordinates.

Example:

```text
BOM -> Mumbai airport coordinates
LHR -> London Heathrow coordinates
```

Why I added it:

Travel exports do not always include distance. Sometimes they only include airport codes. If the row says `BOM` to `LHR`, I can calculate an approximate distance from coordinates.

## Statuses

Raw row statuses:

```text
PENDING -> saved but not parsed yet
PARSED -> parsed successfully
FAILED -> parser could not understand it
OUT_OF_SCOPE -> understood, but not handled in this prototype
```

Emission record statuses:

```text
PENDING -> waiting for analyst review
FLAGGED -> looks suspicious
APPROVED -> analyst accepted it
LOCKED -> final for audit
```
