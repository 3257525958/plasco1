from django.apps import AppConfig


class SyncAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sync_app'
    verbose_name = 'مدیریت همگام‌سازی'

    def ready(self):
        # غیرفعال کردن سرویس سینک خودکار از طریق تنظیمات
        from django.conf import settings
        if not getattr(settings, 'SYNC_AUTO_START', True):
            print("🔴 سرویس سینک خودکار در apps.py غیرفعال شده")
            return

        # فقط در حالت آفلاین سیگنال‌ها را ثبت کن
        if getattr(settings, 'OFFLINE_MODE', False):
            try:
                # import با تاخیر برای جلوگیری از circular imports
                import threading

                def delayed_registration():
                    import time
                    time.sleep(3)
                    from .signals import safe_register_signals
                    safe_register_signals()

                thread = threading.Thread(target=delayed_registration, daemon=True)
                thread.start()

                print("✅ سیگنال‌های سینک برای حالت آفلاین فعال شدند")

            except Exception as e:
                print(f"⚠️ خطا در فعال‌سازی سیگنال‌ها: {e}")
        else:
            print("ℹ️ حالت آنلاین - سیگنال‌های سینک غیرفعال")