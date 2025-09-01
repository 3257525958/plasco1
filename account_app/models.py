from django.db import models
from django.core.validators import MinValueValidator
from dashbord_app.models import Product
from cantact_app.models import Branch

class Inventory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="کالا"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="شعبه"
    )
    quantity = models.IntegerField(
        verbose_name="تعداد موجودی",
        validators=[MinValueValidator(0)],
        default=0
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "موجودی انبار"
        verbose_name_plural = "موجودی‌های انبار"
        unique_together = ['product', 'branch']

    def __str__(self):
        if self.branch:
            return f"{self.product.name} - {self.branch.name}: {self.quantity}"
        else:
            return f"{self.product.name} - انبار اصلی: {self.quantity}"

class InventoryHistory(models.Model):
    ACTION_CHOICES = [
        ('add', 'افزودن موجودی'),
        ('remove', 'کاهش موجودی'),
        ('transfer', 'انتقال بین شعب'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="کالا")
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='transfers_from', verbose_name="از شعبه")
    to_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='transfers_to', verbose_name="به شعبه")
    quantity = models.IntegerField(verbose_name="تعداد")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="عملیات")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "تاریخچه موجودی"
        verbose_name_plural = "تاریخچه موجودی‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.get_action_display()} - {self.quantity}"