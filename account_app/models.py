from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import jdatetime
from cantact_app.models import Branch

User = get_user_model()

import jdatetime
import uuid
from django.db import models
from django.utils.text import slugify


class InventoryCount(models.Model):
    product_name = models.CharField(max_length=100, verbose_name="نام کالا")
    is_new = models.BooleanField(default=True, verbose_name="کالای جدید")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="شعبه")
    quantity = models.PositiveIntegerField(verbose_name="تعداد")
    count_date = models.CharField(max_length=10, verbose_name="تاریخ شمارش", default="")
    counter = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="شمارنده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    barcode_data = models.CharField(max_length=100, blank=True, null=True, verbose_name="داده بارکد")

    class Meta:
        verbose_name = "شمارش انبار"
        verbose_name_plural = "شمارش های انبار"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # تنظیم تاریخ امروز به صورت خودکار
        if not self.count_date:
            jalali_date = jdatetime.datetime.now().strftime('%Y/%m/%d')
            self.count_date = jalali_date

        # تولید خودکار بارکد اگر وجود نداشته باشد
        if not self.barcode_data:
            # ایجاد یک بارکد منحصر به فرد بر اساس ترکیب نام محصول و شناسه
            base_barcode = slugify(self.product_name)[:20]  # استفاده از نام محصول برای بخشی از بارکد
            unique_id = str(uuid.uuid4())[:8]  # ایجاد یک شناسه منحصر به فرد
            self.barcode_data = f"{base_barcode}-{unique_id}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} - {self.branch.name} - {self.quantity}"
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام محصول", unique=True)
    description = models.TextField(verbose_name="توضیحات", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['name']

    def __str__(self):
        return self.name


class FinancialDocument(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'پرداخت نشده'),
        ('partially_paid', 'تا اندازه ای پرداخت شده'),
        ('settled', 'تسویه حساب'),
    ]

    invoice = models.OneToOneField(
        'dashbord_app.Invoice',
        on_delete=models.CASCADE,
        related_name='financial_document'
    )
    document_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="مبلغ کل"
    )
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        default=Decimal('0'),
        verbose_name="مبلغ پرداخت شده"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unpaid',
        verbose_name="وضعیت پرداخت"
    )

    def __str__(self):
        return f"سند مالی {self.invoice.serial_number}"

    class Meta:
        verbose_name = "سند مالی"
        verbose_name_plural = "اسناد مالی"


class FinancialDocumentItem(models.Model):
    document = models.ForeignKey(
        FinancialDocument,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product_name = models.CharField(max_length=200, verbose_name="نام کالا")
    quantity = models.IntegerField(verbose_name="تعداد")
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="قیمت واحد"
    )
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="تخفیف (%)"
    )
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="قیمت کل"
    )

    def __str__(self):
        return f"{self.product_name} - {self.quantity}x"

    class Meta:
        verbose_name = "آیتم سند مالی"
        verbose_name_plural = "آیتم‌های سند مالی"



# -----------------------مدل برای کشف قیمت به روز-------------------------------------------------
from django.db import models
from decimal import Decimal
import math

class ProductPricing(models.Model):
    product_name = models.CharField(max_length=100, verbose_name="نام کالا", unique=True)
    highest_purchase_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="بالاترین قیمت خرید"
    )
    invoice_date = models.CharField(max_length=10, verbose_name="تاریخ فاکتور", blank=True, null=True)
    invoice_number = models.CharField(max_length=50, verbose_name="شماره فاکتور", blank=True, null=True)
    adjustment_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="درصد تعدیل قیمت خرید"
    )
    standard_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="قیمت معیار",
        blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "قیمت‌گذاری محصول"
        verbose_name_plural = "قیمت‌گذاری محصولات"

    def save(self, *args, **kwargs):
        # محاسبه خودکار قیمت معیار
        if self.highest_purchase_price is not None:
            increased_price = self.highest_purchase_price * (1 + self.adjustment_percentage / 100)
            # گرد کردن به بالا به مضرب 1000
            self.standard_price = Decimal(math.ceil(increased_price / 1000) * 1000)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} - {self.standard_price}"