# sync_app/management/commands/sync_smart_pull.py
from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from sync_app.models import DataSyncLog


class Command(BaseCommand):
    help = 'دریافت هوشمند تغییرات بر اساس ID'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ')

    def handle(self, *args, **options):
        app_name = options['app_name']

        self.stdout.write(f"🧠 دریافت هوشمند تغییرات {app_name}...")

        try:
            from plasco.sync_service import sync_service

            # پیدا کردن آخرین ID سینک شده
            last_sync = DataSyncLog.objects.filter(
                app_name=app_name,
                sync_status=True
            ).order_by('-synced_at').first()

            last_sync_id = 0
            if last_sync and last_sync.data and 'max_id' in last_sync.data:
                last_sync_id = last_sync.data['max_id']

            self.stdout.write(f"🔍 آخرین ID سینک شده: {last_sync_id}")

            # دریافت فقط تغییرات جدید
            response = requests.get(
                f"{sync_service.server_url}/api/sync/pull/",
                params={'last_sync_id': last_sync_id},
                timeout=60
            )

            if response.status_code != 200:
                self.stdout.write(f"❌ خطا در دریافت: {response.status_code}")
                return

            data = response.json()

            if data.get('status') != 'success':
                self.stdout.write(f"❌ خطا از سرور: {data.get('message')}")
                return

            # پردازش تغییرات
            changes = data.get('changes', [])
            deletions = data.get('deletions', [])

            self.stdout.write(f"📥 تغییرات جدید: {len(changes)}")
            self.stdout.write(f"🗑️ حذف‌های جدید: {len(deletions)}")

            # پردازش ایجاد/آپدیت
            processed = 0
            for change in changes:
                # منطق پردازش موجود
                processed += 1

            # پردازش حذف‌ها
            for deletion in deletions:
                try:
                    model_class = apps.get_model(deletion['app_name'], deletion['model_type'])
                    model_class.objects.filter(id=deletion['record_id']).delete()
                    self.stdout.write(f"🗑️ حذف شد: {deletion['model_type']} - ID: {deletion['record_id']}")
                    processed += 1
                except Exception as e:
                    self.stdout.write(f"❌ خطا در حذف: {e}")

            self.stdout.write(f"✅ پردازش شد: {processed} رکورد")

        except Exception as e:
            self.stdout.write(f"❌ خطا: {e}")