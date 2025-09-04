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