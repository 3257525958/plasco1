from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from sync_app.models import DataSyncLog
from django.utils import timezone


class Command(BaseCommand):
    help = 'دریافت تغییرات از سرور به لوکال'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ برای دریافت تغییرات')

    def handle(self, *args, **options):
        app_name = options['app_name']

        self.stdout.write(f"📥 دریافت تغییرات {app_name} از سرور به لوکال...")

        if not settings.OFFLINE_MODE:
            self.stdout.write("❌ فقط در حالت آفلاین قابل اجراست")
            return

        try:
            from plasco.sync_service import sync_service

            # پیدا کردن آخرین زمان سینک
            last_sync = DataSyncLog.objects.filter(
                app_name=app_name,
                sync_status=True
            ).order_by('-synced_at').first()

            params = {}
            if last_sync:
                params['last_sync'] = last_sync.synced_at.isoformat()
                self.stdout.write(f"⏰ آخرین سینک: {last_sync.synced_at}")
            else:
                self.stdout.write("🔄 اولین سینک افزایشی")

            # دریافت تغییرات از سرور
            response = requests.get(
                f"{sync_service.server_url}/api/sync/pull/",
                params=params,
                timeout=60
            )

            if response.status_code != 200:
                self.stdout.write(f"❌ خطا در دریافت تغییرات: {response.status_code}")
                return

            data = response.json()

            if data.get('status') != 'success':
                self.stdout.write(f"❌ خطا از سمت سرور: {data.get('message')}")
                return

            # پردازش تغییرات
            all_changes = data.get('changes', [])
            app_changes = [ch for ch in all_changes if ch.get('app_name') == app_name]

            self.stdout.write(f"🔄 تعداد تغییرات جدید: {len(app_changes)}")

            result = sync_service.process_server_data({'changes': app_changes})

            if result['status'] == 'success':
                # ثبت لاگ سینک موفق
                DataSyncLog.objects.create(
                    app_name=app_name,
                    model_type=f"{app_name}.SyncCheckpoint",
                    record_id=0,
                    action='sync_pull',
                    sync_status=True,
                    synced_at=timezone.now(),
                    data={'changes_count': result['processed_count']}
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ دریافت تغییرات کامل شد: {result['processed_count']} رکورد"
                    )
                )
            else:
                self.stdout.write(f"❌ خطا در پردازش تغییرات: {result['message']}")

        except Exception as e:
            self.stdout.write(f"❌ خطا در دریافت تغییرات: {e}")