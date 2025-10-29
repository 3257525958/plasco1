from django.db import models
from django.utils import timezone


class ServerSyncLog(models.Model):
    MODEL_TYPES = [
        ('product', 'محصولات'),
        ('invoice', 'فاکتورها'),
        ('customer', 'مشتریان'),
        ('pos', 'تراکنش‌های پوز'),
        ('stock', 'موجودی انبار'),
        ('user', 'کاربران'),
        ('branch', 'شعبه‌ها'),
        ('expense', 'هزینه‌ها'),
    ]

    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    record_id = models.IntegerField()
    action = models.CharField(max_length=10)
    data = models.JSONField()
    source_ip = models.GenericIPAddressField()
    sync_direction = models.CharField(max_length=20, choices=[('local_to_server', 'لوکال به سرور'),
                                                              ('server_to_local', 'سرور به لوکال')])
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'server_sync_log'


class SyncToken(models.Model):
    token = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    allowed_ips = models.TextField(help_text="IPهای مجاز (هر خط یک IP)")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sync_tokens'