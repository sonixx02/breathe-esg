from django.contrib import admin

from .models import (
    ActivityLog,
    AirportMaster,
    Client,
    EmissionRecord,
    IngestionBatch,
    MaterialCategoryMap,
    PlantMaster,
    RawIngestionRow,
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'created_at']
    search_fields = ['name', 'slug']

@admin.register(PlantMaster)
class PlantMasterAdmin(admin.ModelAdmin):
    list_display = ['id', 'plant_code', 'plant_name', 'client', 'is_active']
    list_filter = ['is_active', 'client']
    search_fields = ['plant_code', 'plant_name']

@admin.register(MaterialCategoryMap)
class MaterialCategoryMapAdmin(admin.ModelAdmin):
    list_display = ['id', 'material_code', 'material_name', 'activity_category', 'scope']
    list_filter = ['scope', 'client']
    search_fields = ['material_code', 'material_name', 'activity_category']

@admin.register(AirportMaster)
class AirportMasterAdmin(admin.ModelAdmin):
    list_display = ['id', 'iata_code', 'airport_name', 'city', 'country']
    search_fields = ['iata_code', 'airport_name', 'city']

@admin.register(IngestionBatch)
class IngestionBatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_type', 'file_name', 'status', 'uploaded_at']
    list_filter = ['source_type', 'status']

@admin.register(RawIngestionRow)
class RawIngestionRowAdmin(admin.ModelAdmin):
    list_display = ['id', 'batch', 'row_number', 'parse_status']
    list_filter = ['parse_status']

@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_type', 'activity_category', 'status', 'normalized_value']
    list_filter = ['status', 'source_type', 'scope']
    search_fields = ['activity_category', 'location_name']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'record', 'action_type', 'acted_by', 'acted_at']
    list_filter = ['action_type']
