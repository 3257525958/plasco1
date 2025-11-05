from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from sync_app.models import DataSyncLog
from django.utils import timezone


class Command(BaseCommand):
    help = 'ارسال تغییرات از لوکال به سرور'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ برای ارسال تغییرات')

    def handle(self, *args, **options):
        app_name = options['app_name']

        self.stdout.write(f"📤 ارسال تغییرات {app_name} از لوکال به سرور...")

        if not settings.OFFLINE_MODE:
            self.stdout.write("❌ فقط در حالت آفلاین قابل اجراست")
            return

        try:
            # پیدا کردن تغییرات ارسال نشده
            unsynced_changes = DataSyncLog.objects.filter(
                app_name=app_name,
                sync_status=False,
                sync_direction='local_to_server'
            )

            self.stdout.write(f"📋 تعداد تغییرات ارسال نشده: {unsynced_changes.count()}")

            sent_count = 0
            for change in unsynced_changes:
                try:
                    payload = {
                        'app_name': app_name,
                        'model_type': change.model_name,
                        'record_id': change.record_id,
                        'action': change.action,
                        'data': change.data or {}
                    }

                    response = requests.post(
                        f"{settings.ONLINE_SERVER_URL}/api/sync/receive/",
                        json=payload,
                        timeout=20
                    )

                    if response.status_code == 200:
                        change.sync_status = True
                        change.synced_at = timezone.now()
                        change.save()
                        sent_count += 1
                        self.stdout.write(f"✅ ارسال شد: {change.model_name} - ID: {change.record_id}")
                    else:
                        self.stdout.write(f"❌ خطا در ارسال: {change.model_name}-{change.record_id}")

                except Exception as e:
                    self.stdout.write(f"❌ خطا در ارسال {change.model_name}-{change.record_id}: {e}")
                    continue

            self.stdout.write(
                self.style.SUCCESS(f"🎉 ارسال تغییرات کامل شد: {sent_count} رکورد به سرور")
            )

        except Exception as e:
            self.stdout.write(f"❌ خطا در ارسال تغییرات: {e}")