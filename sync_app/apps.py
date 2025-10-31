from django.apps import AppConfig

class SyncAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sync_app'
    verbose_name = 'مدیریت همگام‌سازی'

    def ready(self):
        # فقط در حالت آفلاین سیگنال‌ها را ثبت کن
        from django.conf import settings
        if getattr(settings, 'OFFLINE_MODE', False):
            try:
                from . import signals
                print("✅ سیگنال‌های سینک برای حالت آفلاین ثبت شدند")
            except Exception as e:
                print(f"⚠️ خطا در ثبت سیگنال‌ها: {e}")