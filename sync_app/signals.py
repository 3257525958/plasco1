from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from .models import DataSyncLog


def register_all_signals():
    """ثبت سیگنال برای تمام مدل‌ها"""
    for app_config in apps.get_app_configs():
        if any(app_config.name.startswith(excluded) for excluded in [
            'django.contrib.admin', 'django.contrib.auth',
            'django.contrib.contenttypes', 'django.contrib.sessions'
        ]):
            continue

        for model in app_config.get_models():
            if model.__name__ in ['DataSyncLog', 'SyncSession', 'OfflineSetting', 'ServerSyncLog', 'SyncToken']:
                continue

            post_save.connect(handle_model_change, sender=model)
            print(f"✅ سیگنال ثبت شد: {app_config.name}.{model.__name__}")


def handle_model_change(sender, instance, created, **kwargs):
    """مدیریت تغییرات تمام مدل‌ها"""
    try:
        app_label = instance._meta.app_label
        model_name = instance._meta.model_name

        if model_name in ['datasynclog', 'syncsession', 'offlinesetting']:
            return

        action = 'create' if created else 'update'

        # جمع‌آوری داده‌ها
        data = {}
        for field in instance._meta.get_fields():
            if not field.is_relation or field.one_to_one:
                try:
                    value = getattr(instance, field.name)
                    if hasattr(value, 'isoformat'):
                        data[field.name] = value.isoformat()
                    else:
                        data[field.name] = str(value)
                except:
                    data[field.name] = None

        # ثبت در لاگ (فقط در آفلاین)
        from django.conf import settings
        if settings.OFFLINE_MODE:
            DataSyncLog.objects.create(
                model_type=model_name,
                record_id=instance.id,
                action=action,
                data=data,
                sync_direction='local_to_server'
            )
            print(f"📝 تغییر ثبت شد: {model_name} - ID: {instance.id}")

    except Exception as e:
        print(f"❌ خطا در سیگنال: {e}")


# ثبت خودکار هنگام بارگذاری
register_all_signals()