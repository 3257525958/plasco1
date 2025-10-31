from django.core.management.base import BaseCommand
from plasco.sync_service import sync_service


class Command(BaseCommand):
    help = 'اجرای فوری سینک دوطرفه'

    def handle(self, *args, **options):
        self.stdout.write("🔄 شروع سینک فوری...")

        result = sync_service.full_sync()

        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 سینک کامل شد!\n"
                f"   📤 به سرور ارسال شد: {result['sent_to_server']}\n"
                f"   📥 از سرور دریافت شد: {result['received_from_server']}\n"
                f"   📊 مجموع: {result['total']}"
            )
        )