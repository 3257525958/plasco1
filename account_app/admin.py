from django.contrib import admin
from .models import Inventory, InventoryHistory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'branch', 'quantity', 'last_updated']
    list_filter = ['branch', 'last_updated']
    search_fields = ['product__name', 'branch__name']

@admin.register(InventoryHistory)
class InventoryHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'from_branch', 'to_branch', 'quantity', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['product__name', 'from_branch__name', 'to_branch__name']