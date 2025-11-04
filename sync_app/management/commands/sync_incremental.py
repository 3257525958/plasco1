from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.apps import apps
import requests
import json


class Command(BaseCommand):
    help = 'سینک افزایشی - فقط داده‌های تغییر کرده'

    def handle(self, *args, **options):
        app_name = options['app_name']
        full_sync = options['full']
        verbose = options['verbose']

        self.stdout.write(f'🔄 سینک افزایشی {app_name}...')

        if not settings.OFFLINE_MODE:
            self.stdout.write('❌ فقط در حالت آفلاین قابل اجراست')
            return

        try:
            from sync_app.models import DataSyncLog
            from plasco.sync_service import sync_service

            # استفاده از تابع جدید
            if full_sync or self.get_last_sync_id(app_name) == 0:
                self.stdout.write('🚀 حالت سینک کامل فعال شد')
                result = self.initial_full_sync(sync_service, app_name, verbose)
                # پس از سینک کامل، آخرین ID را پیدا و ذخیره کن
                if result.get('status') == 'success':
                    max_id = self.find_max_id(app_name)
                    self.update_sync_id(app_name, max_id)
                    self.stdout.write(f'💾 ذخیره آخرین ID: {max_id}')
            else:
                last_sync_id = self.get_last_sync_id(app_name)
                self.stdout.write(f'⏰ سینک افزایشی از ID: {last_sync_id}')
                result = self.incremental_sync_changes(sync_service, app_name, last_sync_id, verbose)

            self.stdout.write(self.style.SUCCESS(f'✅ سینک {app_name} کامل شد'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطا: {e}'))

        # اضافه کردن این تابع جدید

    def incremental_sync_changes(self, sync_service, app_name, last_sync_id, verbose):
        """
        سینک افزایشی - فقط تغییرات جدید
        """
        if verbose:
            self.stdout.write(f"🔄 شروع سینک افزایشی برای {app_name} از ID {last_sync_id}...")

        result = sync_service.sync_incremental(app_name, last_sync_id)

        if result['status'] == 'success':
            new_records = result.get('new_records_count', 0)
            if verbose:
                self.stdout.write(f"✅ سینک افزایشی موفق: {new_records} رکورد جدید")
        else:
            self.stdout.write(f"❌ خطا در سینک افزایشی: {result['message']}")

        return result

    def initial_full_sync(self, sync_service, app_name, verbose):
        """سینک کامل اولیه"""
        if verbose:
            self.stdout.write(f"🚀 اجرای سینک کامل اولیه برای {app_name}...")
        return sync_service.sync_specific_app(app_name)

    def get_last_sync_id(self, app_name):
        """دریافت آخرین ID سینک شده - نسخه اصلاح شده"""
        from sync_app.models import DataSyncLog
        try:
            # روش مستقیم: پیدا کردن از metadata
            last_sync = DataSyncLog.objects.filter(
                app_name=app_name,
                action='metadata',
                sync_status=True
            ).order_by('-synced_at').first()

            if last_sync and last_sync.data and 'max_id' in last_sync.data:
                max_id = last_sync.data['max_id']
                self.stdout.write(f'📖 last_sync_id پیدا شد: {max_id}')
                return max_id
            else:
                self.stdout.write('⚠️ last_sync_id پیدا نشد، استفاده از 0')
                return 0

        except Exception as e:
            self.stdout.write(f'❌ خطا در get_last_sync_id: {e}')
            return 0
    def update_sync_id(self, app_name, max_id):
        """ذخیره آخرین ID سینک شده"""
        from sync_app.models import DataSyncLog
        try:
            DataSyncLog.objects.create(
                app_name=app_name,
                model_type=f'{app_name}.SyncInfo',
                record_id=0,
                action='metadata',
                sync_status=True,
                synced_at=timezone.now(),
                data={'max_id': max_id, 'type': 'sync_checkpoint', 'app': app_name}
            )
        except Exception as e:
            print(f"⚠️ خطا در ذخیره ID سینک: {e}")

    def incremental_sync_app(self, sync_service, app_name, last_sync_id, verbose):
        """سینک افزایشی واقعی - فقط رکوردهای با ID جدیدتر"""
        try:
            # استفاده از متد sync_incremental جدید با پارامتر ID
            result = sync_service.sync_incremental(app_name, last_sync_id)

            if verbose:
                if result.get('sync_mode') == 'incremental':
                    new_count = result.get('new_records_count', 0)
                    self.stdout.write(f"📈 سینک افزایشی: {new_count} رکورد جدید (ID > {last_sync_id})")
                else:
                    self.stdout.write("📦 سینک کامل")

            # ذخیره آخرین ID سینک شده
            if result.get('status') == 'success' and result.get('max_synced_id'):
                self.update_sync_id(app_name, result['max_synced_id'])
                if verbose:
                    self.stdout.write(f"💾 آخرین ID سینک شده: {result['max_synced_id']}")

            return result

        except Exception as e:
            self.stdout.write(f"⚠️ خطا در سینک افزایشی: {e}")
            # فال‌بک به سینک کامل
            return sync_service.sync_specific_app(app_name)

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ برای سینک')
        parser.add_argument('--full', action='store_true', help='سینک کامل (اولین بار)')
        parser.add_argument('--verbose', action='store_true', help='نمایش جزئیات')

    def handle(self, *args, **options):
        app_name = options['app_name']
        full_sync = options['full']
        verbose = options['verbose']

        self.stdout.write(f'🔄 سینک افزایشی {app_name}...')

        if not settings.OFFLINE_MODE:
            self.stdout.write('❌ فقط در حالت آفلاین قابل اجراست')
            return

        try:
            from sync_app.models import DataSyncLog
            from plasco.sync_service import sync_service

            # دریافت آخرین ID سینک شده
            last_sync_id = self.get_last_sync_id(app_name)

            if full_sync or last_sync_id == 0:
                self.stdout.write('🚀 حالت سینک کامل فعال شد')
                result = self.full_sync_app(sync_service, app_name, verbose)
                # پس از سینک کامل، آخرین ID را پیدا و ذخیره کن
                if result.get('status') == 'success':
                    max_id = self.find_max_id(app_name)
                    self.update_sync_id(app_name, max_id)
                    self.stdout.write(f'💾 ذخیره آخرین ID: {max_id}')
            else:
                self.stdout.write(f'⏰ سینک افزایشی از ID: {last_sync_id}')
                result = self.incremental_sync_app(sync_service, app_name, last_sync_id, verbose)

            self.stdout.write(self.style.SUCCESS(f'✅ سینک {app_name} کامل شد'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطا: {e}'))

    def find_max_id(self, app_name):
        """پیدا کردن حداکثر ID در یک اپ"""
        from django.apps import apps
        try:
            max_id = 0
            for model in apps.get_app_config(app_name).get_models():
                model_max = model.objects.aggregate(models.Max('id'))['id__max'] or 0
                if model_max > max_id:
                    max_id = model_max
            return max_id
        except:
            return 0
    def full_sync_app(self, sync_service, app_name, verbose):
        """سینک کامل (اولین بار)"""
        return sync_service.sync_specific_app(app_name)

