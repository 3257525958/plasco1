
from django.db import models
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import jdatetime
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File
import os
import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

from django.db import models


class Froshande(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="نام",
        blank=False,
        help_text="نام فروشنده را وارد کنید"
    )
    family = models.CharField(
        max_length=100,
        verbose_name="نام خانوادگی",
        blank=False,
        help_text="نام خانوادگی فروشنده را وارد کنید"
    )
    address = models.TextField(
        verbose_name="آدرس",
        blank=True,
        null=True,
        help_text="آدرس کامل فروشنده"
    )
    store_name = models.CharField(
        max_length=200,
        verbose_name="اسم فروشگاه",
        blank=True,
        null=True,
        help_text="نام فروشگاه یا کسب و کار"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    def __str__(self):
        return f"{self.name} {self.family} - {self.store_name or 'بدون نام فروشگاه'}"

    def get_full_name(self):
        return f"{self.name} {self.family}"

    class Meta:
        verbose_name = "فروشنده"
        verbose_name_plural = "فروشندگان"
        ordering = ['family', 'name']
        indexes = [
            models.Index(fields=['name', 'family']),
            models.Index(fields=['store_name']),
        ]


class ContactNumber(models.Model):
    CONTACT_TYPES = [
        ('mobile', 'تلفن همراه'),
        ('phone', 'تلفن ثابت'),
    ]

    froshande = models.ForeignKey(
        Froshande,
        on_delete=models.CASCADE,
        related_name='contact_numbers',
        verbose_name="فروشنده"
    )
    contact_type = models.CharField(
        max_length=10,
        choices=CONTACT_TYPES,
        verbose_name="نوع تماس"
    )
    number = models.CharField(
        max_length=11,
        verbose_name="شماره تماس",
        blank=False
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="شماره اصلی"
    )

    class Meta:
        verbose_name = "شماره تماس"
        verbose_name_plural = "شماره‌های تماس"
        constraints = [
            models.UniqueConstraint(
                fields=['froshande', 'number'],
                name='unique_contact_per_froshande'
            )
        ]


class BankAccount(models.Model):
    froshande = models.ForeignKey(
        Froshande,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        verbose_name="فروشنده"
    )
    account_number = models.CharField(
        max_length=30,
        verbose_name="شماره حساب",
        blank=True,
        null=True
    )
    bank_name = models.CharField(
        max_length=100,
        verbose_name="نام بانک",
        blank=True,
        null=True
    )
    card_number = models.CharField(
        max_length=16,
        verbose_name="شماره کارت",
        blank=True,
        null=True
    )
    sheba_number = models.CharField(
        max_length=26,
        verbose_name="شماره شبا",
        blank=True,
        null=True
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="حساب اصلی"
    )

    class Meta:
        verbose_name = "حساب بانکی"
        verbose_name_plural = "حساب‌های بانکی"
class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام کالا", unique=True)
    barcode = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="بارکد")
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="قیمت واحد",
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "کالا"
        verbose_name_plural = "کالاها"


class Invoice(models.Model):
    seller = models.ForeignKey(Froshande, on_delete=models.CASCADE, verbose_name="فروشنده")
    date = models.DateField(verbose_name="تاریخ", default=timezone.now)
    serial_number = models.CharField(max_length=12, verbose_name="شماره سریال", unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def jalali_date(self):
        """تاریخ شمسی فاکتور"""
        j_date = jdatetime.datetime.fromgregorian(date=self.date)
        return j_date.strftime('%y%m%d')

    def __str__(self):
        return f"فاکتور {self.serial_number} - {self.seller}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)

    class InvoiceItem(models.Model):
        PRODUCT_TYPE_CHOICES = [
            ('new', 'کالای جدید'),
            ('old', 'کالای قدیمی'),
        ]

        # فیلدهای موجود...
        product_type = models.CharField(
            max_length=10,
            choices=PRODUCT_TYPE_CHOICES,
            default='new',
            verbose_name="نوع کالا"
        )
    product_name = models.CharField(
        max_length=200,
        verbose_name="نام کالا",
        default='کالای نامشخص'
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="قیمت واحد"
    )
    selling_price = models.DecimalField(  # اضافه کردن این فیلد
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="قیمت فروش"
    )
    quantity = models.IntegerField(
        verbose_name="تعداد",
        validators=[MinValueValidator(1)]
    )
    discount = models.DecimalField(  # اضافه کردن این فیلد
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="تخفیف"
    )
    item_number = models.IntegerField(  # اضافه کردن این فیلد
        verbose_name="شماره آیتم",
        default=1
    )
    location = models.CharField(  # اضافه کردن این فیلد
        max_length=100,
        verbose_name="مکان",
        blank=True,
        null=True
    )
    remaining_quantity = models.IntegerField(
        verbose_name="تعداد باقیمانده",
        default=0
    )

    def __str__(self):
        return f"{self.product_name} - {self.quantity}"

    @property
    def total_price(self):
        return (self.quantity * self.unit_price) - self.discount
