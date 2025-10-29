from django.contrib import admin
from .models import DataSyncLog, OfflineSetting, SyncSession

@admin.register(DataSyncLog)
class DataSyncLogAdmin(admin.ModelAdmin):
    list_display = ['model_type', 'record_id', 'action', 'sync_direction', 'sync_status', 'created_at']
    list_filter = ['sync_status', 'action', 'model_type', 'sync_direction']
    search_fields = ['model_type', 'record_id', 'error_message']
    readonly_fields = ['created_at', 'synced_at']

@admin.register(OfflineSetting)
class OfflineSettingAdmin(admin.ModelAdmin):
    list_display = ['setting_key', 'setting_value', 'is_active', 'last_sync']
    list_filter = ['is_active']
    search_fields = ['setting_key', 'description']

@admin.register(SyncSession)
class SyncSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'start_time', 'end_time', 'records_synced', 'sync_direction', 'status']
    list_filter = ['status', 'sync_direction']
    readonly_fields = ['start_time', 'end_time']