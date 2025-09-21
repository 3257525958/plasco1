from django.contrib import admin
from .models import Invoicefrosh, InvoiceItemfrosh


class InvoiceItemfroshInline(admin.TabularInline):
    model = InvoiceItemfrosh
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'total_price', 'standard_price')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invoicefrosh)
class InvoicefroshAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'branch', 'created_by', 'created_at', 'total_amount', 'is_finalized', 'is_paid', 'payment_method',
    'customer_name', 'customer_phone')
    list_filter = ('branch', 'created_at', 'is_finalized', 'is_paid', 'payment_method')
    search_fields = ('id', 'customer_name', 'customer_phone')
    readonly_fields = ('id', 'created_at', 'payment_date', 'total_amount')
    inlines = [InvoiceItemfroshInline]

    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('id', 'branch', 'created_by', 'created_at', 'total_amount')
        }),
        ('وضعیت فاکتور', {
            'fields': ('is_finalized', 'is_paid', 'payment_date', 'payment_method')
        }),
        ('اطلاعات خریدار', {
            'fields': ('customer_name', 'customer_phone')
        }),
    )


@admin.register(InvoiceItemfrosh)
class InvoiceItemfroshAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'price', 'total_price', 'standard_price')
    list_filter = ('invoice__branch',)
    search_fields = ('product__product_name', 'invoice__id')
    readonly_fields = ('invoice', 'product', 'quantity', 'price', 'total_price', 'standard_price')

    def has_add_permission(self, request):
        return False