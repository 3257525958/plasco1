from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.apps import apps
import requests
import json


class Command(BaseCommand):
    help = 'سینک افزایشی - فقط داده‌های تغییر کرده'

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

            # دریافت آخرین زمان سینک
            last_sync = self.get_last_sync_time(app_name)

            if full_sync or not last_sync:
                self.stdout.write('🚀 حالت سینک کامل فعال شد')
                result = self.full_sync_app(sync_service, app_name, verbose)
            else:
                self.stdout.write(f'⏰ سینک افزایشی از زمان: {last_sync}')
                result = self.incremental_sync_app(sync_service, app_name, last_sync, verbose)

            # ذخیره زمان سینک
            self.update_sync_time(app_name)

            self.stdout.write(self.style.SUCCESS(f'✅ سینک {app_name} کامل شد: {result}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطا: {e}'))

    def get_last_sync_time(self, app_name):
        """دریافت آخرین زمان سینک موفق برای یک اپ"""
        from sync_app.models import DataSyncLog
        try:
            last_sync = DataSyncLog.objects.filter(
                app_name=app_name,
                sync_status=True
            ).order_by('-synced_at').first()

            if last_sync:
                return last_sync.synced_at
            return None
        except:
            return None

    def update_sync_time(self, app_name):
        """به‌روزرسانی زمان سینک"""
        from sync_app.models import DataSyncLog
        try:
            DataSyncLog.objects.create(
                app_name=app_name,
                model_type=f'{app_name}.sync_tracker',
                record_id=0,
                action='sync_checkpoint',
                sync_status=True,
                synced_at=timezone.now(),
                data={'type': 'sync_checkpoint', 'app': app_name}
            )
        except:
            pass

    def full_sync_app(self, sync_service, app_name, verbose):
        """سینک کامل (اولین بار)"""
        return sync_service.sync_specific_app(app_name)

    def incremental_sync_app(self, sync_service, app_name, last_sync, verbose):
        """سینک افزایشی - فقط تغییرات جدید"""
        # این بخش نیاز به پیاده‌سازی در سرور دارد
        # فعلاً از سینک کامل استفاده می‌کنیم
        self.stdout.write('⚠️ سینک افزایشی نیاز به پیاده‌سازی در سرور دارد. استفاده از سینک کامل...')
        return sync_service.sync_specific_app(app_name)