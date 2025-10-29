from django.core.management.base import BaseCommand
from plasco.sync_service import sync_service
from sync_app.models import DataSyncLog
import time


class Command(BaseCommand):
    help = 'همگام‌سازی دوطرفه کامل با سرور'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='همگام‌سازی دوطرفه کامل',
        )
        parser.add_argument(
            '--stock-only',
            action='store_true',
            help='فقط همگام‌سازی موجودی',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔄 شروع فرآیند همگام‌سازی دوطرفه...")

        if options['stock_only']:
            # همگام‌سازی سریع موجودی
            count = sync_service.sync_stock_changes()
            self.stdout.write(
                self.style.SUCCESS(f"📦 همگام‌سازی موجودی: {count} تغییر ثبت شد")
            )
        else:
            # همگام‌سازی کامل
            result = sync_service.full_sync_cycle()

            self.stdout.write(
                self.style.SUCCESS(
                    f"🎉 همگام‌سازی دوطرفه کامل شد!\n"
                    f"   📤 به سرور ارسال شد: {result['push']['sent_count']} رکورد\n"
                    f"   📥 از سرور دریافت شد: {result['pull']['received_count']} رکورد\n"
                    f"   ⚖️ تضادهای حل شده: {result['conflicts']['resolved_count']}\n"
                    f"   📊 مجموع: {result['total_synced']} رکورد"
                )
            )

        # نمایش وضعیت نهایی
        unsynced_count = DataSyncLog.objects.filter(sync_status=False).count()
        if unsynced_count > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️ {unsynced_count} رکورد در انتظار همگام‌سازی باقی ماند")
            )