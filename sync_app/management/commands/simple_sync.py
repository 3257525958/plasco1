from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'تست ساده سینک'

    def handle(self, *args, **options):
        if not getattr(settings, 'OFFLINE_MODE', False):
            self.stdout.write("حالت آنلاین - سینک لغو شد")
            return

        self.stdout.write("شروع تست سینک...")

        try:
            from plasco.sync_service import sync_service

            # تست اتصال به سرور
            self.stdout.write("تست اتصال به سرور...")
            import requests
            try:
                response = requests.get(f"{sync_service.server_url}/api/sync/pull/", timeout=10)
                if response.status_code == 200:
                    self.stdout.write("اتصال به سرور موفق")
                    data = response.json()
                    self.stdout.write(f"داده های قابل دریافت: {len(data.get('changes', []))} رکورد")
                else:
                    self.stdout.write(f"خطا در اتصال: {response.status_code}")
                    return
            except Exception as e:
                self.stdout.write(f"خطا در اتصال: {e}")
                return

            # اجرای سینک
            self.stdout.write("اجرای سینک...")
            result = sync_service.download_from_server()

            if result.get('status') == 'success':
                self.stdout.write(f"سینک موفق: {result.get('processed_count', 0)} رکورد پردازش شد")
            else:
                self.stdout.write(f"سینک ناموفق: {result.get('message', 'خطای ناشناخته')}")

        except Exception as e:
            self.stdout.write(f"خطا در تست سینک: {e}")