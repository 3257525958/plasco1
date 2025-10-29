from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from account_app.models import Product, Expense, StockTransaction  # ✅ StockTransaction اضافه شد
from invoice_app.models import Invoicefrosh
from pos_payment.models import POSTransaction
from .models import DataSyncLog


@receiver(post_save, sender=Product)
def log_product_change(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'

    # فقط از فیلدهای واقعی استفاده کن
    data = {
        'name': instance.name,
        'description': instance.description,
    }

    DataSyncLog.objects.create(
        model_type='product',
        record_id=instance.id,
        action=action,
        data=data
    )
    print(f"📝 سیگنال: محصول {instance.name} در لاگ ثبت شد")


@receiver(post_save, sender=StockTransaction)  # ✅ سیگنال جدید برای تراکنش‌های انبار
def log_stock_transaction(sender, instance, created, **kwargs):
    if created:  # فقط برای تراکنش‌های جدید
        data = {
            'product_id': instance.product.id,
            'product_name': instance.product.name,
            'transaction_type': instance.transaction_type,
            'quantity': instance.quantity,
            'description': instance.description,
            'user_id': instance.user.id,
            'username': instance.user.username
        }

        DataSyncLog.objects.create(
            model_type='stock',
            record_id=instance.id,
            action='create',
            data=data,
            sync_direction='local_to_server'
        )
        print(f"📝 سیگنال: تراکنش انبار {instance.id} در لاگ ثبت شد")


@receiver(post_save, sender=Invoicefrosh)
def log_invoice_change(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'

    data = {
        'customer_name': instance.customer_name,
        'total_amount': str(instance.total_amount) if hasattr(instance, 'total_amount') else '0',
    }

    if hasattr(instance, 'branch') and instance.branch:
        data['branch_id'] = instance.branch.id

    DataSyncLog.objects.create(
        model_type='invoice',
        record_id=instance.id,
        action=action,
        data=data
    )


@receiver(post_save, sender=POSTransaction)
def log_pos_change(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'

    data = {
        'amount': str(instance.amount),
        'status': instance.status,
    }

    if hasattr(instance, 'transaction_id'):
        data['transaction_id'] = instance.transaction_id

    DataSyncLog.objects.create(
        model_type='pos',
        record_id=instance.id,
        action=action,
        data=data
    )