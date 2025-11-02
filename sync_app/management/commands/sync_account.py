from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import time


class Command(BaseCommand):
    help = 'سینک مدل‌های زیربرنامه account_app'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100, help='تعداد رکوردها در هر درخواست')
        parser.add_argument('--delay', type=float, default=0.5, help='تاخیر بین درخواست‌ها (ثانیه)')
        parser.add_argument('--models', type=str, help='مدل‌های خاص برای سینک (با کاما جدا شوند)')

    def handle(self, *args, **options):
        if not getattr(settings, 'OFFLINE_MODE', False):
            self.stdout.write("حالت آنلاین - سینک لغو شد")
            return

        from plasco.sync_service import sync_service

        self.stdout.write("🎯 شروع سینک مدل‌های account_app...")

        # دریافت تمام داده‌ها از سرور
        self.stdout.write("📥 دریافت داده از سرور...")
        response = requests.get(f"{sync_service.server_url}/api/sync/pull/", timeout=60)

        if response.status_code != 200:
            self.stdout.write(f"❌ خطا در دریافت داده: {response.status_code}")
            return

        data = response.json()
        all_changes = data.get('changes', [])
        self.stdout.write(f"📦 کل رکوردهای قابل دریافت: {len(all_changes)}")

        # فیلتر کردن فقط مدل‌های account_app
        account_changes = []
        target_models = []

        if options['models']:
            target_models = [model.strip() for model in options['models'].split(',')]

        for change in all_changes:
            if change['app_name'] == 'account_app':
                if not target_models or change['model_type'] in target_models:
                    account_changes.append(change)

        self.stdout.write(f"🎯 رکوردهای account_app: {len(account_changes)}")

        if not account_changes:
            self.stdout.write("⚠️ هیچ داده‌ای برای account_app یافت نشد")
            return

        # نمایش مدل‌های موجود
        model_counts = {}
        for change in account_changes:
            model_type = change['model_type']
            if model_type not in model_counts:
                model_counts[model_type] = 0
            model_counts[model_type] += 1

        self.stdout.write("\n📊 مدل‌های account_app:")
        for model, count in model_counts.items():
            self.stdout.write(f"   {model}: {count} رکورد")

        # پردازش مرحله‌ای
        batch_size = options['limit']
        total_processed = 0
        total_errors = 0

        for i in range(0, len(account_changes), batch_size):
            batch = account_changes[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(account_changes) + batch_size - 1) // batch_size

            self.stdout.write(f"\n🔧 پردازش بسته {batch_num}/{total_batches}: {len(batch)} رکورد")

            result = sync_service.process_server_data({'changes': batch})
            processed = result['processed_count']
            errors = len(result['errors'])

            total_processed += processed
            total_errors += errors

            self.stdout.write(f"   ✅ موفق: {processed}")
            if errors > 0:
                self.stdout.write(f"   ❌ خطا: {errors}")
                # نمایش نمونه خطاها
                for error in result['errors'][:2]:
                    self.stdout.write(f"     - {error}")

            # درصد پیشرفت
            progress = min(100, int((i + len(batch)) / len(account_changes) * 100))
            self.stdout.write(f"   📈 پیشرفت: {progress}%")

            # تاخیر بین درخواست‌ها
            if i + batch_size < len(account_changes):
                time.sleep(options['delay'])

        # نتیجه نهایی
        self.stdout.write(f"\n🎉 سینک account_app کامل شد!")
        self.stdout.write(f"   ✅ رکوردهای پردازش شده: {total_processed}")
        self.stdout.write(f"   ❌ خطاها: {total_errors}")
        success_rate = total_processed / (
                    total_processed + total_errors) * 100 if total_processed + total_errors > 0 else 0
        self.stdout.write(f"   📊 نرخ موفقیت: {success_rate:.1f}%")

        # بررسی وضعیت نهایی
        self.check_final_status()

    def check_final_status(self):
        """بررسی وضعیت نهایی داده‌های سینک شده"""
        try:
            from account_app.models import (
                Product, Expense, ExpenseImage, FinancialDocument,
                FinancialDocumentItem, InventoryCount, PaymentMethod,
                ProductPricing, StockTransaction
            )

            self.stdout.write(f"\n📋 وضعیت نهایی account_app:")
            self.stdout.write(f"   Product: {Product.objects.count()} رکورد")
            self.stdout.write(f"   Expense: {Expense.objects.count()} رکورد")
            self.stdout.write(f"   ExpenseImage: {ExpenseImage.objects.count()} رکورد")
            self.stdout.write(f"   FinancialDocument: {FinancialDocument.objects.count()} رکورد")
            self.stdout.write(f"   FinancialDocumentItem: {FinancialDocumentItem.objects.count()} رکورد")
            self.stdout.write(f"   InventoryCount: {InventoryCount.objects.count()} رکورد")
            self.stdout.write(f"   PaymentMethod: {PaymentMethod.objects.count()} رکورد")
            self.stdout.write(f"   ProductPricing: {ProductPricing.objects.count()} رکورد")
            self.stdout.write(f"   StockTransaction: {StockTransaction.objects.count()} رکورد")

        except Exception as e:
            self.stdout.write(f"⚠️ خطا در بررسی وضعیت نهایی: {e}")