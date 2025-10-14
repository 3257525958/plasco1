from django.contrib import admin
from .models import POSDevice, CheckPayment, CreditPayment, Invoicefrosh, InvoiceItemfrosh


@admin.register(POSDevice)
class POSDeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_holder', 'bank_name', 'card_number', 'is_default', 'is_active', 'created_at']
    list_filter = ['is_default', 'is_active', 'bank_name', 'created_at']
    search_fields = ['name', 'account_holder', 'bank_name', 'card_number', 'account_number']
    list_editable = ['is_default', 'is_active']
    readonly_fields = ['created_at']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'is_default', 'is_active')
        }),
        ('اطلاعات حساب', {
            'fields': ('account_holder', 'card_number', 'account_number', 'bank_name')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at',)
        })
    )


class CheckPaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'owner_full_name', 'check_number', 'amount_display', 'remaining_amount_display',
                    'remaining_payment_method', 'check_date', 'created_at']
    list_filter = ['check_date', 'remaining_payment_method', 'created_at']
    search_fields = ['owner_name', 'owner_family', 'check_number', 'national_id', 'phone']
    readonly_fields = ['invoice', 'created_at']

    fieldsets = (
        ('اطلاعات فاکتور', {
            'fields': ('invoice',)
        }),
        ('اطلاعات صاحب چک', {
            'fields': ('owner_name', 'owner_family', 'national_id', 'phone', 'address')
        }),
        ('اطلاعات چک', {
            'fields': ('check_number', 'amount', 'check_date')
        }),
        ('پرداخت باقیمانده', {
            'fields': ('remaining_amount', 'remaining_payment_method', 'pos_device')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at',)
        })
    )

    def owner_full_name(self, obj):
        return f"{obj.owner_name} {obj.owner_family}"

    owner_full_name.short_description = 'نام کامل صاحب چک'

    def amount_display(self, obj):
        return f"{obj.amount:,} تومان"

    amount_display.short_description = 'مبلغ چک'

    def remaining_amount_display(self, obj):
        return f"{obj.remaining_amount:,} تومان"

    remaining_amount_display.short_description = 'مبلغ باقیمانده'


class CreditPaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'customer_full_name', 'phone', 'credit_amount_display',
                    'remaining_amount_display', 'remaining_payment_method', 'due_date', 'created_at']
    list_filter = ['due_date', 'created_at', 'remaining_payment_method']
    search_fields = ['customer_name', 'customer_family', 'national_id', 'phone']
    readonly_fields = ['invoice', 'created_at']

    fieldsets = (
        ('اطلاعات فاکتور', {
            'fields': ('invoice',)
        }),
        ('اطلاعات مشتری', {
            'fields': ('customer_name', 'customer_family', 'national_id', 'phone', 'address')
        }),
        ('اطلاعات نسیه', {
            'fields': ('credit_amount', 'due_date')
        }),
        ('پرداخت باقیمانده', {
            'fields': ('remaining_amount', 'remaining_payment_method', 'pos_device')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at',)
        })
    )

    def customer_full_name(self, obj):
        return f"{obj.customer_name} {obj.customer_family}"

    customer_full_name.short_description = 'نام کامل مشتری'

    def credit_amount_display(self, obj):
        return f"{obj.credit_amount:,} تومان"

    credit_amount_display.short_description = 'مبلغ نسیه'

    def remaining_amount_display(self, obj):
        return f"{obj.remaining_amount:,} تومان"

    remaining_amount_display.short_description = 'مبلغ باقیمانده'


class InvoiceItemfroshInline(admin.TabularInline):
    model = InvoiceItemfrosh
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'total_price', 'standard_price', 'discount']
    can_delete = False

    fieldsets = (
        (None, {
            'fields': ('product', 'quantity', 'price', 'discount', 'total_price', 'standard_price')
        }),
    )


class CheckPaymentInline(admin.StackedInline):
    model = CheckPayment
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ['created_at']

    fieldsets = (
        ('اطلاعات صاحب چک', {
            'fields': ('owner_name', 'owner_family', 'national_id', 'phone', 'address')
        }),
        ('اطلاعات چک', {
            'fields': ('check_number', 'amount', 'check_date')
        }),
        ('پرداخت باقیمانده', {
            'fields': ('remaining_amount', 'remaining_payment_method', 'pos_device')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at',)
        })
    )


class CreditPaymentInline(admin.StackedInline):
    model = CreditPayment
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ['created_at']

    fieldsets = (
        ('اطلاعات مشتری', {
            'fields': ('customer_name', 'customer_family', 'national_id', 'phone', 'address')
        }),
        ('اطلاعات نسیه', {
            'fields': ('credit_amount', 'due_date')
        }),
        ('پرداخت باقیمانده', {
            'fields': ('remaining_amount', 'remaining_payment_method', 'pos_device')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at',)
        })
    )


@admin.register(Invoicefrosh)
class InvoicefroshAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'branch', 'customer_name', 'total_amount_display',
                    'payment_method_display', 'is_paid', 'is_finalized', 'created_at_jalali']
    list_filter = ['branch', 'payment_method', 'is_paid', 'is_finalized', 'created_at']
    search_fields = ['serial_number', 'customer_name', 'customer_phone']
    readonly_fields = ['serial_number', 'created_at', 'created_by', 'total_without_discount']
    inlines = [InvoiceItemfroshInline]

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('serial_number', 'branch', 'created_by', 'created_at')
        }),
        ('اطلاعات مالی', {
            'fields': ('total_without_discount', 'discount', 'total_amount')
        }),
        ('اطلاعات پرداخت', {
            'fields': ('payment_method', 'pos_device', 'is_paid', 'payment_date')
        }),
        ('وضعیت فاکتور', {
            'fields': ('is_finalized',)
        }),
        ('اطلاعات مشتری', {
            'fields': ('customer_name', 'customer_phone')
        })
    )

    def get_inlines(self, request, obj):
        """
        نمایش اینلاین مناسب بر اساس روش پرداخت
        """
        if obj:
            if obj.payment_method == 'check':
                return [InvoiceItemfroshInline, CheckPaymentInline]
            elif obj.payment_method == 'credit':
                return [InvoiceItemfroshInline, CreditPaymentInline]
        return [InvoiceItemfroshInline]

    def payment_method_display(self, obj):
        return obj.get_payment_method_display()

    payment_method_display.short_description = 'روش پرداخت'

    def total_amount_display(self, obj):
        return f"{obj.total_amount:,} تومان"

    total_amount_display.short_description = 'مبلغ کل'

    def created_at_jalali(self, obj):
        return obj.get_jalali_date() + ' ' + obj.get_jalali_time()

    created_at_jalali.short_description = 'تاریخ ایجاد (شمسی)'

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'branch', 'created_by', 'pos_device'
        ).prefetch_related('items')


@admin.register(InvoiceItemfrosh)
class InvoiceItemfroshAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'product', 'quantity', 'price_display', 'discount_display',
                    'total_price_display', 'standard_price_display']
    list_filter = ['invoice__branch', 'invoice__created_at']
    search_fields = ['product__product_name', 'invoice__serial_number']
    readonly_fields = ['invoice', 'product', 'quantity', 'price', 'total_price', 'standard_price', 'discount']

    def price_display(self, obj):
        return f"{obj.price:,} تومان"

    price_display.short_description = 'قیمت واحد'

    def discount_display(self, obj):
        return f"{obj.discount:,} تومان"

    discount_display.short_description = 'تخفیف'

    def total_price_display(self, obj):
        return f"{obj.total_price:,} تومان"

    total_price_display.short_description = 'قیمت کل'

    def standard_price_display(self, obj):
        return f"{obj.standard_price:,} تومان"

    standard_price_display.short_description = 'قیمت معیار'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ثبت مدل‌ها با کلاس‌های Admin سفارشی
admin.site.register(CheckPayment, CheckPaymentAdmin)
admin.site.register(CreditPayment, CreditPaymentAdmin)

# تنظیمات مربوط به ادمین
admin.site.site_header = 'سیستم مدیریت فروش'
admin.site.site_title = 'پنل مدیریت فروش'
admin.site.index_title = 'مدیریت فروش و فاکتورها'