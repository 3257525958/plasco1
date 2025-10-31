from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from django.conf import settings


def register_all_signals():
    """ثبت سیگنال برای تمام مدل‌ها فقط در حالت آفلاین"""
    # فقط در حالت آفلاین سیگنال‌ها را ثبت کن
    if not getattr(settings, 'OFFLINE_MODE', False):
        return

    try:
        from .models import DataSyncLog

        for app_config in apps.get_app_configs():
            # نادیده گرفتن اپ‌های سیستمی
            if any(app_config.name.startswith(excluded) for excluded in [
                'django.contrib.admin', 'django.contrib.auth',
                'django.contrib.contenttypes', 'django.contrib.sessions',
                'sync_app'  # از sync_app خودمان هم صرف نظر کنیم
            ]):
                continue

            for model in app_config.get_models():
                model_name = model.__name__

                # نادیده گرفتن مدل‌های سینک
                if model_name in ['DataSyncLog', 'SyncSession', 'OfflineSetting', 'ServerSyncLog', 'SyncToken']:
                    continue

                try:
                    post_save.connect(handle_model_change, sender=model, weak=False)
                    print(f"✅ سیگنال ثبت شد: {app_config.name}.{model_name}")
                except Exception as e:
                    print(f"⚠️ خطا در ثبت سیگنال برای {model_name}: {e}")
                    continue

    except Exception as e:
        print(f"❌ خطا در ثبت سیگنال‌ها: {e}")


def handle_model_change(sender, instance, created, **kwargs):
    """مدیریت تغییرات مدل‌ها"""
    try:
        # فقط در حالت آفلاین پردازش کن
        if not getattr(settings, 'OFFLINE_MODE', False):
            return

        from .models import DataSyncLog

        app_label = instance._meta.app_label
        model_name = instance._meta.model_name

        # نادیده گرفتن مدل‌های سینک
        if model_name.lower() in ['datasynclog', 'syncsession', 'offlinesetting', 'serversynclog', 'synctoken']:
            return

        action = 'create' if created else 'update'

        # جمع‌آوری داده‌ها به صورت ایمن
        data = {}
        for field in instance._meta.get_fields():
            if not field.is_relation or field.one_to_one:
                try:
                    value = getattr(instance, field.name)
                    if hasattr(value, 'isoformat'):
                        data[field.name] = value.isoformat()
                    else:
                        data[field.name] = str(value)
                except (AttributeError, ValueError):
                    data[field.name] = None

        # ثبت در لاگ
        DataSyncLog.objects.create(
            model_type=model_name,
            record_id=instance.id,
            action=action,
            data=data,
            sync_direction='local_to_server'
        )

        print(f"📝 تغییر ثبت شد: {model_name} - ID: {instance.id}")

    except Exception as e:
        print(f"❌ خطا در پردازش تغییرات: {e}")


# ثبت سیگنال‌ها با تاخیر برای جلوگیری از circular imports
import threading

timer = threading.Timer(2.0, register_all_signals)
timer.start()