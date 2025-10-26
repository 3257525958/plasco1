# pos_payment/models.py
from django.db import models

class POSTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="مبلغ")
    transaction_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ تراکنش")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")
    response_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="کد پاسخ")
    response_message = models.TextField(blank=True, null=True, verbose_name="پیام پاسخ")
    reference_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="شماره مرجع")
    terminal_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="شماره ترمینال")
    raw_request = models.TextField(blank=True, null=True, verbose_name="درخواست خام")
    raw_response = models.TextField(blank=True, null=True, verbose_name="پاسخ خام")

    class Meta:
        verbose_name = "تراکنش پوز"
        verbose_name_plural = "تراکنش‌های پوز"
        ordering = ['-transaction_date']

    def __str__(self):
        return f"تراکنش {self.amount} - {self.get_status_display()} - {self.transaction_date.strftime('%Y-%m-%d %H:%M')}"