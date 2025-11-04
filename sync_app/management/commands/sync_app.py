from django.core.management.base import BaseCommand
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'سینک اپ خاص از سرور به لوکال'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='نام اپ برای سینک (مثلاً: cantact_app)')
        parser.add_argument('--verbose', action='store_true', help='نمایش جزئیات بیشتر')

    def handle(self, *args, **options):
        app_name = options['app_name']
        verbose = options['verbose']

        self.stdout.write(f'🎯 شروع سینک {app_name} از سرور به لوکال...')

        if not settings.OFFLINE_MODE:
            self.stdout.write('❌ این دستور فقط در حالت آفلاین قابل اجراست')
            return

        # پاک کردن کش ماژول‌ها
        modules_to_remove = [m for m in sys.modules if 'sync_service' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        try:
            from plasco.sync_service import sync_service

            if verbose:
                self.stdout.write(f'🔍 تعداد مدل‌های کشف شده: {len(sync_service.sync_models)}')
                self.stdout.write(f'🌐 آدرس سرور: {sync_service.server_url}')

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