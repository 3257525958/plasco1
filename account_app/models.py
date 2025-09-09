from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import jdatetime
from cantact_app.models import Branch

User = get_user_model()


class InventoryCount(models.Model):
    product_name = models.CharField(max_length=100, verbose_name="نام کالا")
    is_new = models.BooleanField(default=True, verbose_name="کالای جدید")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="شعبه")
    quantity = models.PositiveIntegerField(verbose_name="تعداد")
    count_date = models.CharField(max_length=10, verbose_name="تاریخ شمارش", default="")
    counter = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="شمارنده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "شمارش انبار"
        verbose_name_plural = "شمارش های انبار"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # تنظیم تاریخ امروز به صورت خودکار
        if not self.count_date:
            jalali_date = jdatetime.datetime.now().strftime('%Y/%m/%d')
            self.count_date = jalali_date
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