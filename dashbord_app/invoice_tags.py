# invoice_tags.py
from django import template

register = template.Library()

@register.filter(name='sum_total')
def sum_total(items):
    return sum(item.total_price for item in items)