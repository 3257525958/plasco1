from django.core.management.base import BaseCommand
from django.conf import settings
import requests


class Command(BaseCommand):
    help = 'انتقال اولیه کامل داده‌ها از سرور به لوکال'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ برای انتقال اولیه')

    def handle(self, *args, **options):
        app_name = options['app_name']

        self.stdout.write(f"🚀 شروع انتقال اولیه کامل {app_name} از سرور به لوکال...")

        if not settings.OFFLINE_MODE:
            self.stdout.write("❌ فقط در حالت آفلاین قابل اجراست")
            return

        try:
            from plasco.sync_service import sync_service

            # دریافت تمام داده‌ها از سرور (بدون فیلتر)
            self.stdout.write("📥 دریافت تمام داده‌ها از سرور...")
            response = requests.get(f"{sync_service.server_url}/api/sync/pull/", timeout=60)

            if response.status_code != 200:
                self.stdout.write(f"❌ خطا در دریافت داده: {response.status_code}")
                return

            data = response.json()

            if data.get('status') != 'success':
                self.stdout.write(f"❌ خطا از سمت سرور: {data.get('message')}")
                return

            # پردازش تمام داده‌های اپ مورد نظر
            all_changes = data.get('changes', [])
            app_changes = [ch for ch in all_changes if ch.get('app_name') == app_name]

            self.stdout.write(f"📦 تعداد رکوردهای {app_name}: {len(app_changes)}")

            result = sync_service.process_server_data({'changes': app_changes})

            if result['status'] == 'success':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ انتقال اولیه کامل شد: {result['processed_count']} رکورد"
                    )
                )
            else:
                self.stdout.write(f"❌ خطا در پردازش: {result['message']}")

        except Exception as e:
            self.stdout.write(f"❌ خطا در انتقال اولیه: {e}")