# check_status.py
from django.db import models
from cantact_app.models import Branch, accuntmodel
from sync_app.models import DataSyncLog
import requests

print('📊 ماکسیمم ID واقعی در لوکال:')
max_id = 0
for model in [Branch, accuntmodel]:
    result = model.objects.aggregate(models.Max('id'))
    model_max_id = result['id__max'] or 0
    print(f'  - {model.__name__}: {model_max_id}')
    if model_max_id > max_id:
        max_id = model_max_id

print(f'🎯 بزرگترین ID کلی در لوکال: {max_id}')

print(f'\n🔍 نمونه رکوردها:')
for model in [Branch, accuntmodel]:
    print(f'{model.__name__}:')
    for obj in model.objects.order_by('-id')[:2]:
        name = getattr(obj, "name", getattr(obj, "firstname", "---"))
        print(f'  - ID: {obj.id}, نام: {name}')