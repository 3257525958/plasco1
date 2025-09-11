from django.contrib import admin
from .models import InventoryCount

@admin.register(InventoryCount)
class InventoryCountAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'branch', 'quantity', 'count_date', 'counter', 'created_at','is_new','barcode_data']
    list_filter = ['branch', 'is_new', 'count_date']
    search_fields = ['product_name', 'counter__username']

from account_app.models import FinancialDocument,FinancialDocumentItem

admin.site.register(FinancialDocument)
admin.site.register(FinancialDocumentItem)
# admin.site.register(InvoiceItem)

