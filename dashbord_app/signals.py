from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Invoice, InvoiceItem

@receiver(pre_save, sender=Invoice)
def set_invoice_item_numbers(sender, instance, **kwargs):
    """تنظیم شماره کالاها هنگام ذخیره فاکتور"""
    if instance.pk:
        items = instance.items.all().order_by('id')
        for index, item in enumerate(items, start=1):
            if item.item_number != index:
                item.item_number = index
                item.save()