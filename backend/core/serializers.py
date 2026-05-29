from django.contrib.auth.models import User
from rest_framework import serializers

from .models import ActivityLog, EmissionRecord, IngestionBatch, RawIngestionRow


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class IngestionBatchSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = IngestionBatch
        fields = [
            "id",
            "source_type",
            "file_name",
            "uploaded_by",
            "uploaded_at",
            "status",
            "total_rows",
            "parsed_rows",
            "failed_rows",
            "flagged_rows",
            "notes",
        ]


class RawIngestionRowSerializer(serializers.ModelSerializer):
    batch_id = serializers.IntegerField(source="batch.id", read_only=True)
    source_type = serializers.CharField(source="batch.source_type", read_only=True)
    file_name = serializers.CharField(source="batch.file_name", read_only=True)

    class Meta:
        model = RawIngestionRow
        fields = [
            "id",
            "batch_id",
            "source_type",
            "file_name",
            "row_number",
            "raw_data",
            "parse_status",
            "parse_error",
            "created_at",
        ]


class EmissionRecordSerializer(serializers.ModelSerializer):
    batch_id = serializers.IntegerField(source="batch.id", read_only=True)
    file_name = serializers.CharField(source="batch.file_name", read_only=True)
    raw_data = serializers.JSONField(source="raw_row.raw_data", read_only=True)
    approved_by = UserSerializer(read_only=True)

    class Meta:
        model = EmissionRecord
        fields = [
            "id",
            "batch_id",
            "file_name",
            "source_type",
            "scope",
            "activity_category",
            "activity_date",
            "period_start",
            "period_end",
            "raw_value",
            "raw_unit",
            "normalized_value",
            "normalized_unit",
            "location_raw",
            "location_name",
            "status",
            "flag_reason",
            "review_comment",
            "is_manually_edited",
            "approved_by",
            "approved_at",
            "locked_at",
            "created_at",
            "updated_at",
            "raw_data",
        ]
        read_only_fields = [
            "id",
            "batch_id",
            "file_name",
            "source_type",
            "scope",
            "raw_value",
            "raw_unit",
            "status",
            "flag_reason",
            "is_manually_edited",
            "approved_by",
            "approved_at",
            "locked_at",
            "created_at",
            "updated_at",
            "raw_data",
        ]


class ActivityLogSerializer(serializers.ModelSerializer):
    acted_by = UserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "record",
            "action_type",
            "old_values",
            "new_values",
            "comment",
            "acted_by",
            "acted_at",
        ]
