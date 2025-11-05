# در sync_api/signals.py (ایجاد فایل جدید)
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from .models import ChangeTracker


@receiver(post_save)
def track_model_save(sender, **kwargs):
    """ردیابی ایجاد و آپدیت"""
    # فقط مدل‌های syncable را ردیابی کن
    if sender._meta.app_label in ['cantact_app', 'account_app', 'invoice_app']:
        instance = kwargs['instance']
        created = kwargs['created']

        ChangeTracker.objects.create(
            app_name=sender._meta.app_label,
            model_name=sender._meta.model_name,
            record_id=instance.id,
            action='create' if created else 'update'
        )


@receiver(post_delete)
def track_model_delete(sender, **kwargs):
    """ردیابی حذف"""
    if sender._meta.app_label in ['cantact_app', 'account_app', 'invoice_app']:
        instance = kwargs['instance']

        ChangeTracker.objects.create(
            app_name=sender._meta.app_label,
            model_name=sender._meta.model_name,
            record_id=instance.id,
            action='delete'
        )