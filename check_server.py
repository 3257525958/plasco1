# check_server.py
import requests
from collections import Counter

server_url = 'https://plasmarket.ir'
try:
    response = requests.get(f'{server_url}/api/sync/pull/', timeout=10)
    print(f'✅ وضعیت سرور: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        cantact_changes = [ch for ch in data.get("changes", []) if ch.get("app_name") == "cantact_app"]
        print(f'📁 رکوردهای cantact_app در سرور: {len(cantact_changes)}')

        if cantact_changes:
            # پیدا کردن بزرگترین ID در سرور
            ids = [ch['record_id'] for ch in cantact_changes]
            print(f'🎯 بزرگترین ID در سرور: {max(ids)}')
            print(f'📊 محدوده ID در سرور: {min(ids)} - {max(ids)}')

            # نمایش انواع مدل‌ها
            model_types = Counter([ch['model_type'] for ch in cantact_changes])
            print(f'📋 انواع مدل‌ها: {dict(model_types)}')
        else:
            print('❌ هیچ داده‌ای از cantact_app در سرور دریافت نشد')

except Exception as e:
    print(f'❌ خطا: {e}')