# sync_app/management/commands/test_smart_sync.py
from django.core.management.base import BaseCommand
from plasco.sync_service import sync_service


class Command(BaseCommand):
    help = 'تست سینک هوشمند با مدیریت خطاهای پیشرفته'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup',
            action='store_true',
            help='اجرای آماده‌سازی داده‌های پایه قبل از سینک',
        )

    def handle(self, *args, **options):
        self.stdout.write('🧪 شروع تست سینک هوشمند...')

        # اجرای آماده‌سازی اگر درخواست شده
        if options['setup']:
            self.stdout.write('🔄 در حال آماده‌سازی داده‌های پایه...')
            from django.core.management import call_command
            call_command('setup_basic_data')

        # تست سینک
        self.stdout.write('🔄 شروع فرآیند سینک...')
        try:
            result = sync_service.pull_server_changes()

            if result['status'] == 'success':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ سینک موفق: {result['received_count']} رکورد پردازش شده"
                    )
                )

                # نمایش آمار دقیق
                for model_key, stats in result['model_stats'].items():
                    status = "✅" if stats['processed'] == stats['expected'] else "⚠️"
                    self.stdout.write(
                        f"{status} {model_key}: {stats['processed']}/{stats['expected']} "
                        f"(خطا: {stats['errors']}, رد شده: {stats.get('skipped', 0)})"
                    )

            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ سینک ناموفق: {result.get('message', 'خطای ناشناخته')}"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ خطا در تست سینک: {e}")
            )