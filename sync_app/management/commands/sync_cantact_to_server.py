from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from sync_app.models import DataSyncLog
from django.utils import timezone


class Command(BaseCommand):
    help = 'ارسال فقط تغییرات cantact_app از لوکال به سرور'

    def handle(self, *args, **options):
        if not settings.OFFLINE_MODE:
            self.stdout.write("❌ فقط در حالت آفلاین قابل اجراست")
            return

        self.stdout.write("📤 ارسال تغییرات cantact_app به سرور...")

        unsynced = DataSyncLog.objects.filter(
            app_name='cantact_app',
            sync_status=False
        )

        sent_count = 0
        for log in unsynced:
            try:
                payload = {
                    'app_name': 'cantact_app',
                    'model_type': log.model_name,
                    'record_id': log.record_id,
                    'action': log.action,
                    'data': log.data or {}
                }

                response = requests.post(
                    f"{settings.ONLINE_SERVER_URL}/api/sync/receive/",
                    json=payload,
                    timeout=20
                )

                if response.status_code == 200:
                    log.sync_status = True
                    log.synced_at = timezone.now()
                    log.save()
                    sent_count += 1
                    self.stdout.write(f"✅ {log.model_name} - ID: {log.record_id}")

            except Exception as e:
                self.stdout.write(f"❌ خطا در {log.model_name}-{log.record_id}: {e}")
                continue

        self.stdout.write(
            self.style.SUCCESS(f"🎉 ارسال کامل شد: {sent_count} رکورد به سرور")
        )