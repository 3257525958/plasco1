from django.db import models
from django.contrib.auth.models import User
from jdatetime import datetime as jdatetime
from django.utils import timezone
from decimal import Decimal
from account_app.models import Branch, PaymentMethod, InventoryCount

class Invoicefrosh(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="شعبه")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ایجاد کننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پرداخت")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name="روش پرداخت")
    total_amount = models.PositiveIntegerField(default=0, verbose_name="مبلغ کل")
    is_finalized = models.BooleanField(default=False, verbose_name="نهایی شده")
    is_paid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    customer_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام خریدار")
    customer_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="تلفن خریدار")

    class Meta:
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"
        ordering = ['-created_at']

    def __str__(self):
        return f"فاکتور {self.id} - {self.branch.name}"

    def get_jalali_date(self):
        """تاریخ شمسی فاکتور"""
        return jdatetime.fromgregorian(datetime=self.created_at).strftime('%Y/%m/%d')

    def get_jalali_time(self):
        """ساعت شمسی فاکتور"""
        return jdatetime.fromgregorian(datetime=self.created_at).strftime('%H:%M')

    def save(self, *args, **kwargs):
        # اگر فاکتور پرداخت شده است، تاریخ پرداخت را ثبت کن
        if self.is_paid and not self.payment_date:
            self.payment_date = timezone.now()
        super().save(*args, **kwargs)

class InvoiceItemfrosh(models.Model):
    invoice = models.ForeignKey(Invoicefrosh, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(InventoryCount, on_delete=models.CASCADE, verbose_name="کالا")
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    price = models.PositiveIntegerField(verbose_name="قیمت واحد")
    total_price = models.PositiveIntegerField(verbose_name="قیمت کل")
    standard_price = models.PositiveIntegerField(verbose_name="قیمت معیار", default=0)

    class Meta:
        verbose_name = "آیتم فاکتور"
        verbose_name_plural = "آیتم‌های فاکتور"

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}"