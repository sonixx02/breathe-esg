# DECISIONS.md

## 1. CSV Uploads Instead of Live APIs

I used CSV uploads for SAP, utility, and travel data.


Questions I'd clarify:

- Will clients send files monthly or weekly?
- Which language and locale settings are used in the client's SAP system?

***

## 2. SAP Data Handling

I worked with purchasing and fuel data exported from SAP as flat CSV files.

Supported fields include:

- material code
- plant code
- quantity
- unit
- date

SAP systems in some configurations export German field names instead of English ones. I handled this by maintaining a header alias map that normalises both variants to the same internal field name before any parsing begins.

```text
MATNR / material_code  → material_code
WERKS / plant          → plant_code
MENGE / quantity       → quantity
MEINS / unit           → unit
BUDAT / posting_date   → date
```

German number formatting is also handled. SAP often exports quantities like `1.000,50` where the period is a thousands separator and the comma is the decimal point. The parser detects this pattern and converts it to `1000.50` before storing or normalising the value.

```text
Raw from SAP:   1.000,50
After parsing:  1000.50
```

What I ignored:

- IDoc ingestion
- OData and BAPI integrations
- Non-fuel materials such as office supplies, packaging, and raw chemicals
- Goods receipt vs invoice quantity reconciliation
- SAP fiscal year variants

Questions I'd clarify:

- Which SAP export format does the client actually use?
- Should emissions be calculated from purchase order quantity, goods receipt quantity, or invoice quantity?

***

## 3. Utility Data Handling

I used utility billing data exported as CSV from utility portals.


Supported fields include:

- meter ID
- site name
- billing start date
- billing end date
- consumption
- unit
- tariff
- cost

```text
Meter: MTR-001
Period: 2024-01-15 to 2024-02-14
Usage: 48200 kWh
Tariff: HT-Commercial
```

 Splitting usage across months is a reporting concern and is not handled

All energy values are normalised to kWh regardless of input unit.

```text
Raw:        48200000 Wh
Normalised: 48200 kWh   (divided by 1000)

Raw:        48.2 MWh
Normalised: 48200 kWh   (multiplied by 1000)
```

The analyst can see both the raw value with its original unit and the normalised value with the conversion factor applied.

What I ignored:

- PDF bill parsing
- Green Button XML ingestion
- Interval-level meter data
- Tariff calculation logic
- Proration of usage across calendar months

Questions I'd clarify:

- Should usage be split across calendar months for downstream reporting?
- Can a single site have multiple meters that need to be aggregated?

***

## 4. Travel Data Handling

I used travel CSV exports from systems such as Concur or Navan.

Supported categories:

- flights
- hotels
- ground transport

For flights, distance is used directly if provided. If distance is missing but both airport codes are present, the system calculates the great-circle distance using the Haversine formula. Airport coordinates are stored in the `AirportMaster` table so the calculation is entirely offline and fast.

```text
category: flight
origin: BOM
destination: LHR
distance_km: blank

→ BOM lat/lon: 19.0896, 72.8656
→ LHR lat/lon: 51.4775, -0.4614
→ Haversine distance: 7,204 km
```

The Haversine formula calculates the shortest path over the Earth's surface between two coordinates. It is the standard method used in aviation distance calculation and gives a good approximation without needing an external API.

For hotels, nights are used as the activity quantity. For ground transport, distance is used where available.

What I ignored:

- Concur and Navan API integrations
- Rail, ferry, and car rental categories
- Meals and other expense types
- Complex layover reconstruction
- Vendor-supplied CO₂ values as the primary pipeline

Questions I'd clarify:

- If the travel provider already supplies CO₂ values, should those be trusted or recalculated independently?
- Should layovers be stored as separate records or grouped under one trip?

***

## 5. Storing Raw Rows Before Parsing

Every uploaded row is stored before any validation or parsing happens.

This means no data disappears when an error occurs. Failed rows are visible to analysts with the exact error reason, and the original source content is always available for comparison against what ended up in the normalised record.

```text
Row has plant_code = PLT_999
Parser does not find PLT_999 in PlantMaster
Raw row is saved with all original field values
parse_status = FAILED
parse_error = "Unknown plant code: PLT_999"
```

***

## 6. Relational Tables with JSONField

I used standard Django models with typed columns for all structured data and a `JSONField` only for the raw source rows.

When I first thought about the data shape, NoSQL seemed reasonable. SAP rows, utility rows, and travel rows are all different in structure, and a document store would let each row look however it needs to without forcing a fixed schema.

But the hard part of this system is not storing messy raw data. It is normalising it, linking it to the original source row, tracking edits, enforcing tenant boundaries, and moving records through a review and audit workflow. That is all relational work. Clients, batches, raw rows, normalised records, approvals, and audit logs all have clear relationships with each other, and those relationships are easier to enforce and query in SQL.

The flexibility benefit of NoSQL is preserved where it is actually needed. Raw source rows live in a `JSONField` so each source can look different. The final normalised records use typed columns so they can be filtered, sorted, approved, and locked cleanly.

***

## 7. Synchronous Parsing

CSV files are parsed during the upload request.

The files in this workflow are small, so synchronous processing keeps the implementation straightforward and easy to test without introducing task queues or background workers.

For larger datasets, parsing could be moved to a queue-based background worker such as Celery, which would let the upload return immediately while parsing continues asynchronously.

***

## 8. Showing Normalisation in the UI

The analyst dashboard shows both the raw value as it arrived and the normalised value after conversion, along with the transformation that was applied.

Examples of what is shown:

```text
SAP quantity field
  Raw:         "1.000,50" L   (German locale format)
  Parsed as:   1000.50 L      (comma replaced as decimal, period removed as thousands separator)
  Normalised:  1000.50 L      (no unit conversion needed, L is already the base unit)

Utility energy field
  Raw:         48200000 Wh
  Normalised:  48200 kWh      (÷ 1000, Wh → kWh)

  Raw:         48.2 MWh
  Normalised:  48200 kWh      (× 1000, MWh → kWh)
```

This gives analysts enough context to verify that the system interpreted the source data correctly before approving a record.

***

## 9. Flagging Suspicious Records

Simple threshold-based rules highlight records that may need closer review.

```text
utility usage > 100000 kWh in one billing period → FLAGGED
flight distance > 15000 km → FLAGGED
SAP fuel quantity > 500000 L in one row → FLAGGED
hotel stay > 30 nights → FLAGGED
```

A production system could make these rules smarter by comparing records against historical averages for the same site, meter, plant, or travel route. For this prototype, fixed thresholds are enough to demonstrate the flagging workflow.

***

## 10. Locking Approved Records

Once a record is approved, it can be locked.

Locked records cannot be modified through the normal edit API, which preserves the audit trail.

I did not implement an unlock workflow. In a production environment, unlocking would typically require elevated permissions and a documented reason for the change.

***

## 11. Scope Derivation from Material Mapping

Scope is not assigned based on the source type. A SAP row is not automatically Scope 1 just because it came from SAP.

Scope is derived from the material-to-category mapping table. Each material code maps to an activity category and a scope value.

```text
DIESEL-HSD → DIESEL_COMBUSTION  → Scope 1
LPG-CYL    → LPG_COMBUSTION    → Scope 1
OFFICE-PPR → OFFICE_SUPPLIES   → OUT_OF_SCOPE (not handled in this prototype)
```

A real SAP procurement file contains both fuel rows and non-fuel rows. Treating everything as Scope 1 would be incorrect. The mapping table also means scope assignments are explicit and auditable rather than inferred at parse time.

In a real deployment, this table would need to be populated with the client's full material list before ingestion begins. For this prototype, a small set of common fuel materials is seeded as demo data.

Questions I'd clarify:

- Should non-fuel SAP materials be treated as Scope 3 Category 1 procurement emissions or simply marked out of scope for the first version?
- Who owns and maintains the material-to-category mapping as new materials are added?

***

## 12. Multi-Tenancy Approach

Every record in the system belongs to one client through a foreign key on the `Client` model.

Tenant isolation is enforced at the query level. Every API view filters by the authenticated user's client before returning any data.

```text
User logs in → system resolves their client
All queries include WHERE client_id = X
One client never sees another client's records
```

I chose a shared schema approach rather than schema-per-tenant or database-per-tenant because it is simpler to operate and sufficient for a prototype with a small number of clients.

Questions I'd clarify:

- Does Breathe ESG have regulatory or contractual requirements that would need database-level isolation between clients?

***

## 13. Database Choice

When I first thought about this problem, NoSQL seemed like a reasonable option. The incoming data from SAP, utility portals, and travel platforms is all different in shape, and a document store would let each row look however it needs to without forcing a fixed schema.

But once I mapped out what the system actually needs to do, SQL made more sense. The hard part is not storing messy raw data. It is normalising it, linking it to the original source row, tracking edits, enforcing tenant boundaries, and moving records through a review and audit workflow. Those are all relational problems. The relationships between clients, batches, raw rows, normalised records, and audit logs are easier to enforce and query in SQL.

The flexibility benefit of NoSQL is still available where it is actually needed. Raw source rows are stored in a `JSONField` so each source can have a different shape. The final normalised records use typed columns so they can be filtered, approved, and locked cleanly.

For local development I use SQLite because it needs no setup. For deployment I use PostgreSQL because hosted filesystems are ephemeral by default and a SQLite file would be lost on redeploy.

```text
Local: DATABASE_URL not set → SQLite
Deployed: DATABASE_URL set → Postgres on Render
```

The schema and Django ORM queries are identical in both environments. Switching requires no code changes.

***

## 14. FAILED vs OUT_OF_SCOPE

Not every invalid row is the same kind of problem.

A row gets `FAILED` when a required field is missing, unparseable, or references something the system does not recognise.

A row gets `OUT_OF_SCOPE` when the data is structurally valid but the material or category is outside the supported subset for this prototype.

```text
plant_code = PLT_999 not found in PlantMaster         → FAILED
material = OFFICE-PPR, valid row but not a fuel item  → OUT_OF_SCOPE
```

This distinction helps analysts quickly separate rows that need fixing from rows that are expected to be skipped.

***

## 15. Record Status Flow

Records move through a defined set of statuses from ingestion to audit lock.

```text
PENDING      → parse succeeded, waiting for analyst review
FAILED       → parse failed, no emission record created
OUT_OF_SCOPE → valid row but outside supported subset, no emission record created
FLAGGED      → parse succeeded but a threshold rule triggered, needs closer review
APPROVED     → analyst reviewed and accepted the record
LOCKED       → record is immutable through the normal API
```

Analysts can approve `PENDING` and `FLAGGED` records. `LOCKED` records cannot be edited through the normal workflow.

***

## 16. Demo Data Loader

The app includes a demo data loader endpoint so reviewers can see the full workflow without preparing or uploading their own files.

When triggered, it creates one batch for each source type with a realistic mix of valid, failed, flagged, and approved rows. The loader uses the same ingestion pipeline as real uploads so the parsing and validation logic is exercised in the same way.

```text
POST /api/demo/load/all
→ SAP batch:     3 valid rows, 1 failed (unknown plant), 1 flagged (large quantity)
→ Utility batch: 2 valid rows, 1 failed (missing billing end date)
→ Travel batch:  3 valid rows, 1 failed (unknown airport), 1 flagged (long distance)
```
