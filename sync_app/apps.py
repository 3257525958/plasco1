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
                # import با تاخیر برای جلوگیری از circular imports
                import threading

                def delayed_registration():
                    import time
                    time.sleep(3)  # تاخیر 3 ثانیه برای اطمینان از لود کامل
                    from .signals import safe_register_signals
                    safe_register_signals()

                # اجرا در thread جداگانه
                thread = threading.Thread(target=delayed_registration, daemon=True)
                thread.start()

                print("✅ سرویس سیگنال‌های سینک فعال شد")

            except Exception as e:
                print(f"⚠️ خطا در فعال‌سازی سیگنال‌ها: {e}")
        else:
            print("ℹ️ حالت آنلاین - سیگنال‌های سینک غیرفعال")