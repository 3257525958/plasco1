from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone
from sync_app.models import DataSyncLog


class Command(BaseCommand):
    help = 'رفع فوری مشکل last_sync_id'

    def handle(self, *args, **options):
        self.stdout.write('🔧 رفع فوری مشکل last_sync_id...')

        # برای cantact_app
        from cantact_app.models import Branch, accuntmodel

        # پیدا کردن بزرگترین ID
        max_id = 0
        for model in [Branch, accuntmodel]:
            result = model.objects.aggregate(models.Max('id'))
            model_max_id = result['id__max'] or 0
            self.stdout.write(f'📊 {model.__name__}: ماکسیمم ID = {model_max_id}')
            if model_max_id > max_id:
                max_id = model_max_id

        self.stdout.write(f'🎯 بزرگترین ID کلی: {max_id}')

        if max_id > 0:
            # حذف تمام رکوردهای قدیمی
            DataSyncLog.objects.filter(app_name='cantact_app').delete()

            # ایجاد رکورد جدید
            DataSyncLog.objects.create(
                app_name='cantact_app',
                model_type='cantact_app.SyncInfo',
                record_id=0,
                action='metadata',
                sync_status=True,
                synced_at=timezone.now(),
                data={'max_id': max_id, 'type': 'fixed_manual', 'app': 'cantact_app'}
            )

            self.stdout.write(self.style.SUCCESS(f'✅ last_sync_id تنظیم شد به: {max_id}'))

            # تأیید
            last = DataSyncLog.objects.filter(app_name='cantact_app').first()
            self.stdout.write(f'📝 تأیید: last_sync_id = {last.data["max_id"]}')
        else:
            self.stdout.write(self.style.ERROR('❌ داده‌ای برای تنظیم last_sync_id وجود ندارد'))