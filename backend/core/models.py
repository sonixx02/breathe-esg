
from django.db import models

from django.contrib.auth.models import User


class SourceType(models.TextChoices):
    SAP = 'SAP', 'SAP'
    UTILITY = 'UTILITY', 'Utility'
    TRAVEL = 'TRAVEL', 'Travel'
    DEMO = 'DEMO', 'Demo'

class BatchStatus(models.TextChoices):
    UPLOADED = 'UPLOADED', 'Uploaded'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    COMPLETED_WITH_ERRORS = 'COMPLETED_WITH_ERRORS', 'Completed with Errors'
    FAILED = 'FAILED', 'Failed'

class RawRowStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PARSED = 'PARSED', 'Parsed'
    FAILED = 'FAILED', 'Failed'
    OUT_OF_SCOPE = 'OUT_OF_SCOPE', 'Out of Scope'

class RecordStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    FLAGGED = 'FLAGGED', 'Flagged'
    APPROVED = 'APPROVED', 'Approved'
    LOCKED = 'LOCKED', 'Locked'

class Scope(models.IntegerChoices):
    SCOPE_1 = 1, 'Scope 1'
    SCOPE_2 = 2, 'Scope 2'
    SCOPE_3 = 3, 'Scope 3'

class Client(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PlantMaster(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    plant_code = models.CharField(max_length=100)
    plant_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('client', 'plant_code')

    def __str__(self):
        return f"{self.plant_code} - {self.plant_name}"

class MaterialCategoryMap(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    material_code = models.CharField(max_length=100)
    material_name = models.CharField(max_length=255)
    activity_category = models.CharField(max_length=100)
    scope = models.IntegerField(choices=Scope.choices)
    default_unit = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('client', 'material_code')

    def __str__(self):
        return f"{self.material_code} - {self.material_name}"

class AirportMaster(models.Model):
    iata_code = models.CharField(max_length=10, unique=True)
    airport_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.iata_code

class IngestionBatch(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    file_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=BatchStatus.choices, default=BatchStatus.UPLOADED)
    total_rows = models.IntegerField(default=0)
    parsed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    flagged_rows = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.source_type} Batch {self.id} - {self.file_name}"

class RawIngestionRow(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE)
    row_number = models.IntegerField()
    raw_data = models.JSONField()
    parse_status = models.CharField(max_length=30, choices=RawRowStatus.choices, default=RawRowStatus.PENDING)
    parse_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Raw Row {self.row_number} (Batch {self.batch.id})"

class EmissionRecord(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    raw_row = models.OneToOneField(RawIngestionRow, on_delete=models.CASCADE)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE)
    
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    scope = models.IntegerField(choices=Scope.choices)
    activity_category = models.CharField(max_length=100)
    
    # Dates
    activity_date = models.DateField(blank=True, null=True)
    period_start = models.DateField(blank=True, null=True)
    period_end = models.DateField(blank=True, null=True)
    
    # Values
    raw_value = models.FloatField()
    raw_unit = models.CharField(max_length=50)
    normalized_value = models.FloatField()
    normalized_unit = models.CharField(max_length=50)
    
    # Location
    location_raw = models.CharField(max_length=255, blank=True, null=True)
    location_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=RecordStatus.choices, default=RecordStatus.PENDING)
    flag_reason = models.TextField(blank=True, null=True)
    review_comment = models.TextField(blank=True, null=True)
    is_manually_edited = models.BooleanField(default=False)
    
    # Audit
    approved_by = models.ForeignKey(User, related_name='approved_records', on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    locked_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Record {self.id} - {self.activity_category} ({self.status})"

class ActivityLog(models.Model):
    class ActionType(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        EDITED = 'EDITED', 'Edited'
        FLAGGED = 'FLAGGED', 'Flagged'
        APPROVED = 'APPROVED', 'Approved'
        LOCKED = 'LOCKED', 'Locked'
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    acted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    acted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} on Record {self.record.id}"
