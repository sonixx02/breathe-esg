import csv
import io
from pathlib import Path

from django.db import transaction

from .models import ActivityLog, Client, EmissionRecord, IngestionBatch, RawIngestionRow
from .parsers.sap_parser import parse_sap_row
from .parsers.travel_parser import parse_travel_row
from .parsers.utility_parser import parse_utility_row
from .utils import clean_csv_row


PARSERS = {
    "SAP": parse_sap_row,
    "UTILITY": parse_utility_row,
    "TRAVEL": parse_travel_row,
}


def get_default_client():
    client, _ = Client.objects.get_or_create(
        slug="acme",
        defaults={"name": "Acme Corp"},
    )
    return client


def decode_upload(file_obj):
    data = file_obj.read()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


@transaction.atomic
def process_csv_upload(client, user, source_type, file_name, file_obj):
    source_type = source_type.upper()
    parser = PARSERS[source_type]

    batch = IngestionBatch.objects.create(
        client=client,
        source_type=source_type,
        file_name=file_name,
        uploaded_by=user,
        status="PROCESSING",
    )

    text = decode_upload(file_obj)
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        batch.status = "FAILED"
        batch.notes = "CSV file has no header row."
        batch.save(update_fields=["status", "notes"])
        return batch

    total_rows = 0
    parsed_rows = 0
    failed_rows = 0
    flagged_rows = 0

    for row_number, row in enumerate(reader, start=2):
        if not any(value for value in row.values() if value):
            continue

        total_rows += 1
        raw_row = RawIngestionRow.objects.create(
            client=client,
            batch=batch,
            row_number=row_number,
            raw_data=clean_csv_row(row),
            parse_status="PENDING",
        )

        try:
            is_valid, parsed_data, error_message = parser(row, client)
        except Exception as exc:
            is_valid = False
            parsed_data = None
            error_message = f"Parser error: {exc}"

        if not is_valid:
            failed_rows += 1
            raw_row.parse_status = "FAILED"
            raw_row.parse_error = error_message or "Could not parse row."
            raw_row.save(update_fields=["parse_status", "parse_error"])
            continue

        record = EmissionRecord.objects.create(
            client=client,
            raw_row=raw_row,
            batch=batch,
            source_type=source_type,
            **parsed_data,
        )
        raw_row.parse_status = "PARSED"
        raw_row.save(update_fields=["parse_status"])
        parsed_rows += 1

        ActivityLog.objects.create(
            client=client,
            record=record,
            action_type="CREATED",
            new_values={"record_id": record.id, "status": record.status},
            acted_by=user,
        )

        if record.status == "FLAGGED":
            flagged_rows += 1
            ActivityLog.objects.create(
                client=client,
                record=record,
                action_type="FLAGGED",
                new_values={"flag_reason": record.flag_reason},
                acted_by=user,
            )

    batch.total_rows = total_rows
    batch.parsed_rows = parsed_rows
    batch.failed_rows = failed_rows
    batch.flagged_rows = flagged_rows
    if total_rows == 0:
        batch.status = "FAILED"
        batch.notes = "CSV file had headers but no data rows."
    elif failed_rows:
        batch.status = "COMPLETED_WITH_ERRORS"
    else:
        batch.status = "COMPLETED"
    batch.save()
    return batch


def load_demo_file(client, user, source_type):
    source_type = source_type.upper()
    file_name = f"sample_{source_type.lower()}.csv"
    path = Path(__file__).resolve().parents[1] / "sample_data" / file_name
    with path.open("rb") as sample_file:
        return process_csv_upload(client, user, source_type, f"demo_{file_name}", sample_file)
