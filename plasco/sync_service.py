import requests
import json
from django.conf import settings
from sync_app.models import DataSyncLog, SyncSession
from django.utils import timezone
import hashlib
import logging
import threading
import time
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist

logger = logging.getLogger(__name__)


class SmartSyncProcessor:
    def __init__(self):
        self.type_converters = {
            'DateTimeField': self.convert_datetime,
            'DateField': self.convert_date,
            'IntegerField': self.convert_integer,
            'FloatField': self.convert_float,
            'BooleanField': self.convert_boolean,
            'DecimalField': self.convert_decimal,
        }

    def convert_datetime(self, value):
        from django.utils.dateparse import parse_datetime
        return parse_datetime(value) if value else None

    def convert_date(self, value):
        from django.utils.dateparse import parse_date
        return parse_date(value) if value else None

    def convert_integer(self, value):
        return int(value) if value and str(value).strip() else 0

    def convert_float(self, value):
        return float(value) if value and str(value).strip() else 0.0

    def convert_boolean(self, value):
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes', 'y')

    def convert_decimal(self, value):
        from decimal import Decimal
        return Decimal(value) if value and str(value).strip() else Decimal('0.0')

    def smart_value_converter(self, field_type, value):
        """تبدیل هوشمند مقادیر بر اساس نوع فیلد"""
        if value is None or value == '':
            return None

        converter = self.type_converters.get(field_type)
        if converter:
            try:
                return converter(value)
            except (ValueError, TypeError):
                return value
        return value


class BidirectionalSyncService:
    def __init__(self):
        self.server_url = "https://plasmarket.ir"
        self.api_key = "hUafL49RYuXQSRyyc7ZoRF_SxFdF8wUomtjF5YICRVk"
        self.last_sync_time = None
        self.sync_interval = 60
        self.is_running = False
        self.smart_processor = SmartSyncProcessor()

        # اضافه کردن این خط برای مدیریت داده‌های پایه
        self.ensure_default_data()

    def ensure_default_data(self):
        """ایجاد داده‌های پایه ضروری برای سینک"""
        try:
            from cantact_app.models import Branch
            from dashbord_app.models import Froshande

            # ایجاد شعبه پیش‌فرض
            default_branch, created = Branch.objects.get_or_create(
                name='شعبه مرکزی',
                defaults={
                    'address': 'آدرس پیش‌فرض - ویرایش شود',
                    'phone': '02100000000',
                    'is_active': True
                }
            )
            if created:
                print(f"✅ شعبه پیش‌فرض ایجاد شد: {default_branch.name}")

            # ایجاد فروشنده پیش‌فرض
            default_froshande, created = Froshande.objects.get_or_create(
                name='فروشنده پیش‌فرض',
                defaults={
                    'phone': '09120000000',
                    'address': 'آدرس پیش‌فرض',
                    'is_active': True
                }
            )
            if created:
                print(f"✅ فروشنده پیش‌فرض ایجاد شد: {default_froshande.name}")

        except Exception as e:
            print(f"⚠️ خطا در ایجاد داده‌های پایه: {e}")

    def handle_required_fields(self, model_class, processed_data):
        """مدیریت خودکار فیلدهای اجباری که مقدار ندارند"""
        model_name = model_class.__name__

        # لیست فیلدهای اجباری بر اساس مدل
        required_fields_map = {
            'InventoryCount': ['branch_id'],
            'Expense': ['branch_id'],
            'ExpenseImage': ['expense_id'],
            'ContactNumber': ['froshande_id'],
            'BankAccount': ['froshande_id'],
            'FinancialDocumentItem': ['document_id'],
            'InvoiceItem': ['invoice_id'],
        }

        required_fields = required_fields_map.get(model_name, [])

        for field_name in required_fields:
            if field_name not in processed_data or processed_data[field_name] is None:
                print(f"⚠️ فیلد اجباری {field_name} مقدار ندارد - استفاده از مقدار پیش‌فرض")

                if field_name.endswith('_id'):
                    # برای فیلدهای رابطه‌ای، اولین رکورد موجود را استفاده کن
                    related_field_name = field_name.replace('_id', '')
                    try:
                        related_field = model_class._meta.get_field(related_field_name)
                        related_model = related_field.related_model
                        if related_model and related_model.objects.exists():
                            first_obj = related_model.objects.first()
                            processed_data[field_name] = first_obj.id
                            print(f"✅ استفاده از {related_model.__name__}.id={first_obj.id} برای {field_name}")
                        else:
                            print(f"❌ هیچ رکوردی در {related_model.__name__} وجود ندارد")
                    except FieldDoesNotExist:
                        print(f"❌ فیلد {related_field_name} پیدا نشد")

        return processed_data

    def validate_required_data(self, model_class, processed_data):
        """اعتبارسنجی داده‌های ضروری قبل از ذخیره‌سازی"""
        try:
            # ایجاد نمونه موقت برای اعتبارسنجی
            temp_obj = model_class(**processed_data)
            temp_obj.full_clean()
            return True
        except Exception as e:
            print(f"⚠️ اعتبارسنجی ناموفق: {e}")
            return False

    def process_model_data_improved(self, model_class, raw_data):
        """پردازش هوشمند داده‌های مدل با مدیریت روابط - نسخه بهبود یافته"""
        processed_data = {}

        for field_name, value in raw_data.items():
            try:
                # پیدا کردن فیلد
                field = model_class._meta.get_field(field_name)
                field_type = type(field).__name__

                # مدیریت فیلدهای رابطه‌ای
                if field.is_relation:
                    if value is None or value == '':
                        processed_data[field_name] = None
                    else:
                        try:
                            # پیدا کردن مدل مرتبط
                            related_model = field.related_model
                            if related_model:
                                # اگر رکورد مرتبط وجود دارد، آن را پیدا کن
                                if hasattr(value, 'id'):
                                    processed_data[field_name] = value
                                else:
                                    # سعی کن رکورد را از دیتابیس پیدا کنی
                                    try:
                                        if isinstance(value, dict) and 'id' in value:
                                            related_id = value['id']
                                        else:
                                            related_id = value

                                        related_obj = related_model.objects.get(id=related_id)
                                        processed_data[field_name] = related_obj.id
                                    except related_model.DoesNotExist:
                                        print(f"⚠️ رکورد مرتبط پیدا نشد: {related_model.__name__}.id={value}")
                                        processed_data[field_name] = None
                        except Exception as e:
                            print(f"⚠️ خطا در پردازش رابطه {field_name}: {e}")
                            processed_data[field_name] = None
                else:
                    # تبدیل مقدار بر اساس نوع فیلد
                    processed_data[field_name] = self.smart_processor.smart_value_converter(field_type, value)

            except FieldDoesNotExist:
                # اگر فیلد وجود ندارد، نادیده بگیر
                print(f"⚠️ فیلد {field_name} در مدل {model_class.__name__} وجود ندارد")
                continue
            except Exception as e:
                # در صورت خطا، مقدار اصلی را نگه دار
                processed_data[field_name] = value
                print(f"⚠️ خطا در پردازش فیلد {field_name}: {e}")

        return processed_data

    def pull_server_changes(self):
        """دریافت و پردازش هوشمند همه داده‌ها"""
        try:
            print("🤖 دریافت پکیج سینک هوشمند...")
            response = requests.get(
                f"{self.server_url}/api/sync/pull/",
                headers={'Authorization': f'Token {self.api_key}'},
                timeout=60  # افزایش تایم‌اوت برای سینک بزرگ
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('sync_mode') == 'AUTO_DISCOVERY':
                    return self.process_smart_sync(result['payload'])
                else:
                    return self.process_legacy_sync(result)

            else:
                return {'received_count': 0, 'status': 'error', 'message': f"HTTP {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return {'received_count': 0, 'status': 'error', 'message': str(e)}


    def process_model_data(self, model_class, raw_data):
        """پردازش هوشمند داده‌های مدل با مدیریت روابط"""
        processed_data = {}

        for field_name, value in raw_data.items():
            try:
                # پیدا کردن فیلد
                field = model_class._meta.get_field(field_name)
                field_type = type(field).__name__

                # مدیریت فیلدهای رابطه‌ای
                if field.is_relation:
                    if value is None or value == '':
                        processed_data[field_name] = None
                    else:
                        try:
                            # پیدا کردن مدل مرتبط
                            related_model = field.related_model
                            if related_model:
                                # اگر رکورد مرتبط وجود دارد، آن را پیدا کن
                                if hasattr(value, 'id'):
                                    processed_data[field_name] = value
                                else:
                                    # سعی کن رکورد را از دیتابیس پیدا کنی
                                    try:
                                        related_obj = related_model.objects.get(id=value)
                                        processed_data[field_name] = related_obj
                                    except related_model.DoesNotExist:
                                        print(f"⚠️ رکورد مرتبط پیدا نشد: {related_model.__name__}.id={value}")
                                        processed_data[field_name] = None
                        except Exception as e:
                            print(f"⚠️ خطا در پردازش رابطه {field_name}: {e}")
                            processed_data[field_name] = None
                else:
                    # تبدیل مقدار بر اساس نوع فیلد
                    processed_data[field_name] = self.smart_processor.smart_value_converter(field_type, value)

            except FieldDoesNotExist:
                # اگر فیلد وجود ندارد، نادیده بگیر
                print(f"⚠️ فیلد {field_name} در مدل {model_class.__name__} وجود ندارد")
                continue
            except Exception as e:
                # در صورت خطا، مقدار اصلی را نگه دار
                processed_data[field_name] = value
                print(f"⚠️ خطا در پردازش فیلد {field_name}: {e}")

        return processed_data
    def print_smart_sync_report(self, model_stats, total_processed):
        """چاپ گزارش زیبا از سینک"""
        print("\n" + "=" * 60)
        print("📊 ﮔﺰارش ﻧﻬﺎیی ﺳیﻨک ﻫﻮﺷﻤﻨﺪ")
        print("=" * 60)

        for model_key, stats in model_stats.items():
            status_icon = "✅" if stats['processed'] == stats['expected'] else "⚠️"
            print(f"{status_icon} {model_key}:")
            print(f"   📈 پردازش شده: {stats['processed']}/{stats['expected']}")
            if stats['errors'] > 0:
                print(f"   ❌ خطاها: {stats['errors']}")

        print("-" * 60)
        print(f"🎯 کل رکوردهای پردازش شده: {total_processed}")
        print(f"🕒 آخرین بروزرسانی: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    def process_legacy_sync(self, result):
        """پردازش سینک قدیمی (برای سازگاری)"""
        server_data = result.get('changes', [])
        # ... کد قدیمی برای سازگاری

    # بقیه متدها مانند قبل...
    def start_auto_sync(self):
        """شروع همگام‌سازی خودکار"""
        if self.is_running:
            print("⚠️ سرویس همگام‌سازی در حال اجراست")
            return

        self.is_running = True
        print(f"🤖 راه‌اندازی سینک هوشمند خودکار هر {self.sync_interval} ثانیه")

        def sync_worker():
            while self.is_running:
                try:
                    print(f"⏰ سینک خودکار در {timezone.now()}")
                    result = self.pull_server_changes()

                    if result['status'] == 'success':
                        print(f"✅ سینک موفق: {result['received_count']} رکورد")
                    else:
                        print(f"❌ خطا در سینک: {result.get('message', 'Unknown error')}")

                except Exception as e:
                    print(f"❌ خطا در سینک خودکار: {e}")

                time.sleep(self.sync_interval)

        self.sync_thread = threading.Thread(target=sync_worker, daemon=True)
        self.sync_thread.start()

    def stop_auto_sync(self):
        """توقف همگام‌سازی خودکار"""
        self.is_running = False
        print("🛑 سینک هوشمند خودکار متوقف شد")

    def process_smart_sync(self, payload):
        """پردازش پکیج سینک هوشمند با مدیریت خطاهای پیشرفته"""
        print(
            f"🎯 پردازش سینک هوشمند: {payload['summary']['total_records']} رکورد از {payload['summary']['total_models']} مدل")

        model_stats = {}
        total_processed = 0

        # پردازش هر مدل
        for model_info in payload.get('models', []):
            app_name = model_info['app']
            model_name = model_info['model']
            model_key = f"{app_name}.{model_name}"

            try:
                model_class = apps.get_model(app_name, model_name)
                model_stats[model_key] = {
                    'expected': model_info['record_count'],
                    'processed': 0,
                    'errors': 0,
                    'skipped': 0
                }

                print(f"🔄 پردازش مدل: {model_key}")

            except Exception as e:
                print(f"❌ مدل پیدا نشد: {model_key} - {e}")
                model_stats[model_key] = {'expected': 0, 'processed': 0, 'errors': 1, 'skipped': 0}
                continue

        # پردازش همه تغییرات
        for change in payload.get('changes', []):
            try:
                app_name = change['app_name']
                model_name = change['model_type']
                model_key = f"{app_name}.{model_name}"

                if model_key not in model_stats:
                    continue

                model_class = apps.get_model(app_name, model_name)

                # پردازش داده‌ها با مدیریت خطا - استفاده از نسخه بهبود یافته
                processed_data = self.process_model_data_improved(model_class, change['data'])

                # مدیریت فیلدهای اجباری
                processed_data = self.handle_required_fields(model_class, processed_data)

                # بررسی اینکه آیا داده‌های ضروری وجود دارند
                if self.validate_required_data(model_class, processed_data):
                    # ایجاد یا آپدیت رکورد
                    obj, created = model_class.objects.update_or_create(
                        id=change['record_id'],
                        defaults=processed_data
                    )

                    model_stats[model_key]['processed'] += 1
                    total_processed += 1

                    # نمایش نمونه‌ای از پردازش
                    if model_stats[model_key]['processed'] <= 3:
                        action = "ایجاد" if created else "آپدیت"
                        print(f"  ✅ {model_key} (ID: {change['record_id']}) - {action}")

                    # ذخیره در لاگ
                    DataSyncLog.objects.create(
                        model_type=model_key,
                        record_id=change['record_id'],
                        action=change['action'],
                        data=change['data'],
                        sync_direction='server_to_local',
                        sync_status=True,
                        synced_at=timezone.now()
                    )
                else:
                    model_stats[model_key]['skipped'] += 1
                    print(f"  ⏭️ {model_key} (ID: {change['record_id']}) - رد شد به دلیل داده‌های ناقص")

            except Exception as e:
                print(f"  ❌ خطا در پردازش {model_key}: {e}")
                if model_key in model_stats:
                    model_stats[model_key]['errors'] += 1

        # نمایش گزارش نهایی
        self.print_smart_sync_report(model_stats, total_processed)

        self.last_sync_time = timezone.now()
        return {
            'received_count': total_processed,
            'status': 'success',
            'sync_mode': 'SMART_AUTO',
            'model_stats': model_stats
        }

    # ... متدهای دیگر مانند full_sync_cycle, push_local_changes, etc.


# ایجاد نمونه سرویس
sync_service = BidirectionalSyncService()