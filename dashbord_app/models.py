

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


class Froshande(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام", blank=False)
    family = models.CharField(max_length=100, verbose_name="نام خانوادگی", blank=False)
    address = models.TextField(verbose_name="آدرس", blank=True, null=True)
    store_name = models.CharField(max_length=200, verbose_name="اسم فروشگاه", blank=True, null=True)
    card_number = models.CharField(max_length=16, verbose_name="شماره کارت", blank=True, null=True)
    sheba_number = models.CharField(max_length=26, verbose_name="شماره شبا", blank=False)
    phone = models.CharField(max_length=11, verbose_name="تلفن ثابت", blank=True, null=True)
    mobile = models.CharField(max_length=11, verbose_name="تلفن همراه", blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} {self.family} - {self.store_name}"

    class Meta:
        verbose_name = "فروشنده"
        verbose_name_plural = "فروشندگان"


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
    selling_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="قیمت فروش",
        default=0
    )
    quantity = models.IntegerField(
        verbose_name="تعداد",
        validators=[MinValueValidator(1)]
    )
    item_number = models.PositiveIntegerField(
        verbose_name="شماره کالا",
        default=0
    )
    barcode_image = models.ImageField(
        upload_to='barcodes/',
        verbose_name="تصویر بارکد",
        blank=True,
        null=True
    )
    barcode_value = models.CharField(
        max_length=20,
        verbose_name="مقدار بارکد",
        blank=True,
        null=True
    )

    @property
    def total_price(self):
        return self.selling_price * self.quantity

    @property
    def barcode_base(self):
        """تولید کد بارکد بر اساس شماره سریال فاکتور و شماره ردیف کالا"""
        try:
            # شماره سریال فاکتور (12 رقم)
            serial_part = self.invoice.serial_number

            # شماره ردیف کالا (4 رقم)
            item_part = str(self.item_number).zfill(4)

            return f"{serial_part}{item_part}"
        except Exception as e:
            logger.error(f"Error in barcode_base: {str(e)}")
            return "0000000000000000"
    def generate_barcode_image(self):
        """تولید تصویر بارکد و ذخیره آن"""
        try:
            # تولید بارکد استاندارد Code128
            code128 = barcode.get('code128', self.barcode_value, writer=ImageWriter())

            # تنظیمات برای بارکد - بدون نمایش متن
            options = {
                'module_width': 0.2,
                'module_height': 15,
                'font_size': 10,
                'text_distance': 5,
                'quiet_zone': 5,
                'write_text': False  # این خط را اضافه کنید
            }

            # ایجاد بافر برای ذخیره موقت
            buffer = BytesIO()
            code128.write(buffer, options=options)

            # نام فایل
            filename = f'barcode_{self.barcode_value}.png'

            # ذخیره در فیلد تصویر
            self.barcode_image.save(filename, File(buffer), save=False)

        except Exception as e:
            logger.error(f"Error generating barcode: {str(e)}")
    def save(self, *args, **kwargs):
        # تولید مقدار بارکد
        if not self.barcode_value:
            try:
                self.barcode_value = self.barcode_base
            except Exception as e:
                logger.error(f"Error setting barcode_value: {str(e)}")
                self.barcode_value = "ERROR"

        # تولید تصویر بارکد
        if not self.barcode_image:
            self.generate_barcode_image()

        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.product_name} - {self.quantity}x"

    class Meta:
        ordering = ['item_number']



