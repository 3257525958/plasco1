from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
import requests


class Command(BaseCommand):
    help = 'بررسی یکسانی داده‌های سرور و لوکال'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ برای بررسی')

    def handle(self, *args, **options):
        app_name = options['app_name']

        self.stdout.write(f'🔍 بررسی یکسانی داده‌های {app_name} بین سرور و لوکال...')

        try:
            # دریافت داده از سرور
            server_url = getattr(settings, 'ONLINE_SERVER_URL', 'https://plasmarket.ir')
            response = requests.get(f"{server_url}/api/sync/pull/", timeout=30)

            if response.status_code != 200:
                self.stdout.write(f'❌ خطا در دریافت داده از سرور: {response.status_code}')
                return

            server_data = response.json()
            self.compare_data(server_data, app_name)

        except Exception as e:
            self.stdout.write(f'❌ خطا در بررسی: {e}')

    def compare_data(self, server_data, app_name):
        server_changes = server_data.get('changes', [])
        app_server_data = [ch for ch in server_changes if ch.get('app_name') == app_name]

        self.stdout.write(f'📊 آمار سرور: {len(app_server_data)} رکورد در {app_name}')

        # گروه‌بندی داده‌های سرور بر اساس مدل
        server_by_model = {}
        for change in app_server_data:
            model_name = change['model_type']
            if model_name not in server_by_model:
                server_by_model[model_name] = []
            server_by_model[model_name].append(change)

        # بررسی داده‌های لوکال
        local_stats = {}
        for model_name in server_by_model.keys():
            try:
                model_class = apps.get_model(app_name, model_name)
                local_count = model_class.objects.count()
                local_stats[model_name] = local_count
            except Exception as e:
                local_stats[model_name] = f'خطا: {e}'

        # نمایش نتایج مقایسه
        self.stdout.write('\n📋 نتایج مقایسه:')
        self.stdout.write('=' * 50)

        all_match = True
        for model_name, server_changes in server_by_model.items():
            server_count = len(server_changes)
            local_count = local_stats.get(model_name, 0)

            if local_count == server_count:
                status = '✅ یکسان'
            else:
                status = '❌ متفاوت'
                all_match = False

            self.stdout.write(f'📁 {model_name}:')
            self.stdout.write(f'   سرور: {server_count} رکورد')
            self.stdout.write(f'   لوکال: {local_count} رکورد')
            self.stdout.write(f'   وضعیت: {status}')
            self.stdout.write('')

        # نمایش نمونه‌ای از داده‌ها
        if all_match:
            self.stdout.write(self.style.SUCCESS('🎉 تمام داده‌ها یکسان هستند!'))
            self.show_sample_data(app_server_data[:3])  # نمایش 3 نمونه
        else:
            self.stdout.write(self.style.WARNING('⚠️ برخی داده‌ها متفاوت هستند!'))

    def show_sample_data(self, sample_changes):
        self.stdout.write('\n🔎 نمونه‌ای از داده‌های سینک شده:')
        for i, change in enumerate(sample_changes[:3], 1):
            self.stdout.write(f'   {i}. {change["model_type"]} - ID: {change["record_id"]}')
            # نمایش برخی فیلدهای مهم
            data = change.get('data', {})
            important_fields = {k: v for k, v in data.items() if k in ['name', 'title', 'phone', 'email']}
            for field, value in important_fields.items():
                self.stdout.write(f'      {field}: {value}')