from django.db import models
from django.utils import timezone


class DataSyncLog(models.Model):
    SYNC_DIRECTIONS = [
        ('local_to_server', 'لوکال به سرور'),
        ('server_to_local', 'سرور به لوکال'),
    ]

    MODEL_TYPES = [
        ('product', 'محصولات'),
        ('invoice', 'فاکتورها'),
        ('customer', 'مشتریان'),
        ('pos', 'تراکنش‌های پوز'),
        ('stock', 'موجودی انبار'),
    ]

    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    record_id = models.IntegerField()
    action = models.CharField(max_length=10)
    data = models.JSONField(null=True, blank=True)
    sync_direction = models.CharField(max_length=20, choices=SYNC_DIRECTIONS, default='local_to_server')
    sync_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    conflict_resolved = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'data_sync_log'
        indexes = [
            models.Index(fields=['sync_status', 'model_type']),
        ]


class SyncSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    records_synced = models.IntegerField(default=0)
    sync_direction = models.CharField(max_length=20, choices=DataSyncLog.SYNC_DIRECTIONS)
    status = models.CharField(max_length=20, default='in_progress')

    class Meta:
        db_table = 'sync_sessions'


class OfflineSetting(models.Model):
    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    description = models.TextField(blank=True)
    last_sync = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'offline_settings'
        verbose_name = 'تنظیمات آفلاین'
        verbose_name_plural = 'تنظیمات آفلاین'

    def __str__(self):
        return self.setting_key


# اضافه کردن مدل ServerSyncLog که گم شده بود
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