from django.core.management.base import BaseCommand
from django.conf import settings
import importlib


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
        parser.add_argument(
            '--force',
            action='store_true',
            help='اجباری کردن سینک حتی در صورت وجود خطا',
        )

    def handle(self, *args, **options):
        # فقط در حالت آفلاین اجرا شود
        if not getattr(settings, 'OFFLINE_MODE', False):
            self.stdout.write(
                self.style.WARNING("⏭️ حالت آنلاین - سینک لغو شد")
            )
            return

        self.stdout.write("🔄 شروع فرآیند همگام‌سازی دوطرفه...")

        # ایمپورت داینامیک برای جلوگیری از circular imports
        sync_service = self.get_sync_service()

        if not sync_service:
            self.stdout.write(
                self.style.ERROR("❌ سرویس سینک در دسترس نیست")
            )
            return

        try:
            if options['stock_only']:
                # همگام‌سازی سریع موجودی
                if hasattr(sync_service, 'sync_stock_changes'):
                    count = sync_service.sync_stock_changes()
                    self.stdout.write(
                        self.style.SUCCESS(f"📦 همگام‌سازی موجودی: {count} تغییر ثبت شد")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠️ قابلیت سینک موجودی پیاده‌سازی نشده")
                    )
            else:
                # همگام‌سازی کامل
                if hasattr(sync_service, 'enhanced_full_sync'):
                    result = sync_service.enhanced_full_sync()
                else:
                    # استفاده از متد قدیمی
                    result = sync_service.full_sync()
                    # تبدیل به فرمت جدید
                    result = {
                        'push': {'sent_count': result.get('sent_to_server', 0)},
                        'pull': {'received_count': result.get('received_from_server', 0)},
                        'conflicts': {'resolved_count': 0},
                        'total_synced': result.get('total', 0)
                    }

                self.stdout.write(
                    self.style.SUCCESS(
                        f"🎉 همگام‌سازی دوطرفه کامل شد!\n"
                        f"   📤 به سرور ارسال شد: {result['push']['sent_count']} رکورد\n"
                        f"   📥 از سرور دریافت شد: {result['pull']['received_count']} رکورد\n"
                        f"   ⚖️ تضادهای حل شده: {result['conflicts']['resolved_count']}\n"
                        f"   📊 مجموع: {result['total_synced']} رکورد"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ خطا در سینک: {e}")
            )
            if options['force']:
                self.stdout.write("🔄 ادامه فرآیند به دلیل حالت اجباری...")
            else:
                return

        # نمایش وضعیت نهایی
        self.show_sync_status()

    def get_sync_service(self):
        """دریافت سرویس سینک به صورت ایمن"""
        try:
            from plasco.sync_service import sync_service
            return sync_service
        except ImportError as e:
            self.stdout.write(f"⚠️ خطا در ایمپورت سرویس سینک: {e}")
            return None

    def show_sync_status(self):
        """نمایش وضعیت سینک"""
        try:
            from sync_app.models import DataSyncLog
            unsynced_count = DataSyncLog.objects.filter(sync_status=False).count()
            if unsynced_count > 0:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ {unsynced_count} رکورد در انتظار همگام‌سازی باقی ماند")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("✅ تمام رکوردها همگام‌سازی شدند")
                )
        except Exception as e:
            self.stdout.write(f"⚠️ خطا در بررسی وضعیت: {e}")