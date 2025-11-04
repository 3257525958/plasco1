from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
import requests


class Command(BaseCommand):
    help = 'بررسی دقیق تفاوت‌های بین سرور و لوکال'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ برای بررسی')
        parser.add_argument('model_name', type=str, help='نام مدل برای بررسی')

    def handle(self, *args, **options):
        app_name = options['app_name']
        model_name = options['model_name']

        self.stdout.write(f'🔍 بررسی تفاوت‌های {app_name}.{model_name}...')

        try:
            # دریافت داده از سرور
            server_url = getattr(settings, 'ONLINE_SERVER_URL', 'https://plasmarket.ir')
            response = requests.get(f"{server_url}/api/sync/pull/", timeout=30)

            if response.status_code != 200:
                self.stdout.write(f'❌ خطا در دریافت داده از سرور: {response.status_code}')
                return

            server_data = response.json()
            self.find_differences(server_data, app_name, model_name)

        except Exception as e:
            self.stdout.write(f'❌ خطا در بررسی: {e}')

    def find_differences(self, server_data, app_name, model_name):
        # داده‌های سرور
        server_changes = server_data.get('changes', [])
        server_records = [ch for ch in server_changes if
                          ch.get('app_name') == app_name and ch.get('model_type') == model_name]

        # داده‌های لوکال
        try:
            model_class = apps.get_model(app_name, model_name)
            local_records = model_class.objects.all()

            # جمع‌آوری IDها
            server_ids = {ch['record_id'] for ch in server_records}
            local_ids = {obj.id for obj in local_records}

            self.stdout.write(f'\n📊 آمار {app_name}.{model_name}:')
            self.stdout.write(f'   سرور: {len(server_ids)} رکورد - IDs: {sorted(server_ids)}')
            self.stdout.write(f'   لوکال: {len(local_ids)} رکورد - IDs: {sorted(local_ids)}')

            # پیدا کردن تفاوت‌ها
            only_in_server = server_ids - local_ids
            only_in_local = local_ids - server_ids
            common_ids = server_ids & local_ids

            self.stdout.write(f'\n🔎 تفاوت‌ها:')
            self.stdout.write(f'   فقط در سرور: {sorted(only_in_server)}')
            self.stdout.write(f'   فقط در لوکال: {sorted(only_in_local)}')
            self.stdout.write(f'   مشترک: {sorted(common_ids)}')

            # بررسی تفاوت در داده‌های مشترک
            if common_ids:
                self.stdout.write(f'\n📝 بررسی داده‌های مشترک:')
                for record_id in sorted(common_ids)[:3]:  # فقط 3 تا اول
                    server_record = next((ch for ch in server_records if ch['record_id'] == record_id), None)
                    local_record = local_records.get(id=record_id)

                    if server_record and local_record:
                        self.compare_record_data(server_record, local_record, record_id)

        except Exception as e:
            self.stdout.write(f'❌ خطا در پردازش مدل {model_name}: {e}')

    def compare_record_data(self, server_record, local_record, record_id):
        server_data = server_record.get('data', {})
        differences = []

        for field_name, server_value in server_data.items():
            if hasattr(local_record, field_name):
                local_value = getattr(local_record, field_name)

                # تبدیل برای مقایسه
                if hasattr(local_value, 'isoformat'):  # DateTime
                    local_value = local_value.isoformat()

                if server_value != local_value:
                    differences.append(f"{field_name}: سرور='{server_value}' vs لوکال='{local_value}'")

        if differences:
            self.stdout.write(f'   🔸 ID {record_id} تفاوت دارد:')
            for diff in differences[:3]:  # فقط 3 تفاوت اول
                self.stdout.write(f'      {diff}')
        else:
            self.stdout.write(f'   ✅ ID {record_id} یکسان است')