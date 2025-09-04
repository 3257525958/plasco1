from django.contrib import admin
from .models import InventoryCount

@admin.register(InventoryCount)
class InventoryCountAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'branch', 'quantity', 'count_date', 'counter', 'created_at']
    list_filter = ['branch', 'is_new', 'count_date']
    search_fields = ['product_name', 'counter__username']