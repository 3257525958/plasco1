from django.contrib import admin
from .models import POSDevice, CheckPayment, CreditPayment, Invoicefrosh, InvoiceItemfrosh


@admin.register(POSDevice)
class POSDeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_holder', 'bank_name', 'is_default', 'is_active']
    list_filter = ['is_default', 'is_active', 'bank_name']
    search_fields = ['name', 'account_holder', 'bank_name']
    list_editable = ['is_default', 'is_active']


@admin.register(CheckPayment)
class CheckPaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'owner_name', 'owner_family', 'check_number', 'amount', 'check_date']
    list_filter = ['check_date']
    search_fields = ['owner_name', 'owner_family', 'check_number', 'national_id']
    readonly_fields = ['invoice']


@admin.register(CreditPayment)
class CreditPaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'customer_name', 'customer_family', 'due_date']
    list_filter = ['due_date']
    search_fields = ['customer_name', 'customer_family', 'national_id']
    readonly_fields = ['invoice']


class InvoiceItemfroshInline(admin.TabularInline):
    model = InvoiceItemfrosh
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'total_price', 'standard_price', 'discount']


@admin.register(Invoicefrosh)
class InvoicefroshAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'branch', 'customer_name', 'total_amount', 'payment_method', 'is_paid',
                    'created_at']
    list_filter = ['branch', 'payment_method', 'is_paid', 'is_finalized', 'created_at']
    search_fields = ['serial_number', 'customer_name', 'customer_phone']
    readonly_fields = ['serial_number', 'created_at', 'created_by']
    inlines = [InvoiceItemfroshInline]

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)