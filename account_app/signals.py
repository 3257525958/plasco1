
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from .models import ProductPricing, InventoryCount
from decimal import Decimal
import math


@receiver(post_save, sender=ProductPricing)
def update_inventory_prices(sender, instance, created, **kwargs):
    """
    زمانی که قیمت معیار در ProductPricing تغییر کرد،
    قیمت فروش در InventoryCount را به روز می‌کند
    """
    if instance.standard_price is not None:
        inventory_items = InventoryCount.objects.filter(
            product_name=instance.product_name
        )

        for item in inventory_items:
            new_price = instance.standard_price * (1 + item.profit_percentage / Decimal('100'))
            rounded_price = Decimal(math.ceil(new_price / 1000) * 1000)

            if item.selling_price != rounded_price:
                item.selling_price = rounded_price
                item.save()  # استفاده از save به جای update
