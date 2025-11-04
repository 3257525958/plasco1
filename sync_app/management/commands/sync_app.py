from django.core.management.base import BaseCommand
from django.conf import settings
import sys


# در فایل: sync_app/management/commands/sync_app.py
# اضافه کردن به کلاس Command

class Command(BaseCommand):
    help = 'سینک اپ خاص از سرور به لوکال'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ برای سینک (مثلاً: cantact_app)')
        parser.add_argument('--verbose', action='store_true', help='نمایش جزئیات بیشتر')
        parser.add_argument('--full', action='store_true', help='سینک کامل اولیه')  # اضافه کردن این خط

    def handle(self, *args, **options):
        app_name = options['app_name']
        verbose = options['verbose']
        full_sync = options.get('full', False)  # اضافه کردن این خط

        self.stdout.write(f'🎯 شروع سینک {app_name} از سرور به لوکال...')

        if not settings.OFFLINE_MODE:
            self.stdout.write('❌ این دستور فقط در حالت آفلاین قابل اجراست')
            return

        try:
            from plasco.sync_service import sync_service

            if verbose:
                self.stdout.write(f'🔍 تعداد مدل‌های کشف شده: {len(sync_service.sync_models)}')
                self.stdout.write(f'🌐 آدرس سرور: {sync_service.server_url}')

            # اضافه کردن این بخش
            if full_sync:
                result = self.initial_full_sync(app_name, sync_service)
            else:
                result = sync_service.sync_specific_app(app_name)

            if result['status'] == 'success':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ سینک {app_name} با موفقیت انجام شد: {result['processed_count']} رکورد پردازش شد"
                    )
                )
                if result['errors']:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ {len(result['errors'])} خطا در پردازش")
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ خطا در سینک: {result['message']}")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ خطا در اجرای سینک: {e}')
            )

    # اضافه کردن این تابع جدید
    def initial_full_sync(self, app_name, sync_service):
        """
        سینک کامل اولیه - برای اولین بار
        """
        self.stdout.write(f"🚀 شروع سینک کامل اولیه برای {app_name}...")

        # ۱. دریافت مدل‌ها
        models = sync_service.get_all_models_for_app(app_name)
        if not models:
            return {'status': 'error', 'message': 'هیچ مدلی پیدا نشد'}

        # ۲. بررسی سینک قبلی
        sync_status = sync_service.check_previous_sync(app_name, models)

        # ۳. اگر قبلاً سینک شده، هشدار بده
        already_synced = [name for name, status in sync_status.items() if status['is_synced']]
        if already_synced:
            self.stdout.write(f"⚠️ {len(already_synced)} مدل قبلاً سینک شده‌اند: {', '.join(already_synced)}")
            response = input("آیا می‌خواهید بازنویسی کنید؟ (y/n): ")
            if response.lower() != 'y':
                return {'status': 'cancelled', 'message': 'کاربر لغو کرد'}

        # ۴. سینک کامل با last_sync_id = 0
        result = sync_service.sync_incremental(app_name, last_sync_id=0)

        if result['status'] == 'success':
            self.stdout.write(f"🎉 سینک کامل اولیه موفق: {result['processed_count']} رکورد")
        else:
            self.stdout.write(f"❌ خطا در سینک کامل: {result['message']}")

        return result