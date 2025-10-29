from django.contrib import admin
from .models import ServerSyncLog, SyncToken

@admin.register(ServerSyncLog)
class ServerSyncLogAdmin(admin.ModelAdmin):
    list_display = ['model_type', 'record_id', 'action', 'source_ip', 'processed', 'created_at']
    list_filter = ['processed', 'model_type', 'sync_direction']

@admin.register(SyncToken)
class SyncTokenAdmin(admin.ModelAdmin):
    list_display = ['name', 'token', 'is_active', 'last_used', 'created_at']