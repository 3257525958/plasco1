from django.contrib import admin

from dashbord_app.models import Froshande,Invoice,InvoiceItem

admin.site.register(Froshande)
admin.site.register(Invoice)
# admin.site.register(InvoiceItem)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number',
        'product_name',
        'quantity',
        'remaining_quantity',  # اضافه کردن این خط
        'unit_price',
        'unit_price',
    ]

    def invoice_number(self, obj):
        return obj.invoice.serial_number

    invoice_number.short_description = 'شماره فاکتور'



