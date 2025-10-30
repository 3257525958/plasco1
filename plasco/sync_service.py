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

        # کشف خودکار مدل‌ها در ابتدا
        self.discovered_models = self.discover_local_models()

        # ایجاد داده‌های پایه برای مدل‌های کشف شده
        self.ensure_dynamic_default_data()

    # plasco/sync_service.py
    # در کلاس BidirectionalSyncService این متد را اضافه کنید:

    def process_dynamic_sync(self, payload):
        """پردازش سینک پویا با کشف خودکار مدل‌ها"""
        print(
            f"🎯 پردازش سینک پویا: {payload['summary']['total_records']} رکورد از {payload['summary']['total_models']} مدل")

        model_stats = {}
        total_processed = 0

        # پردازش هر مدل به صورت پویا
        for model_info in payload.get('models', []):
            app_name = model_info['app']
            model_name = model_info['model']
            model_key = f"{app_name}.{model_name}"

            try:
                # کشف پویای مدل
                model_class = apps.get_model(app_name, model_name)
                model_stats[model_key] = {
                    'expected': model_info['record_count'],
                    'processed': 0,
                    'errors': 0,
                    'skipped': 0,
                    'priority': model_info.get('sync_priority', 'medium')
                }

                print(f"🔄 پردازش مدل: {model_key} (اولویت: {model_stats[model_key]['priority']})")

            except Exception as e:
                print(f"❌ مدل پیدا نشد: {model_key} - {e}")
                model_stats[model_key] = {'expected': 0, 'processed': 0, 'errors': 1, 'skipped': 0}
                continue

        # پردازش تغییرات با اولویت‌بندی
        changes_by_priority = {
            'high': [],
            'medium': [],
            'low': []
        }

        for change in payload.get('changes', []):
            priority = change.get('sync_priority', 'medium')
            changes_by_priority[priority].append(change)

        # پردازش بر اساس اولویت
        for priority in ['high', 'medium', 'low']:
            print(f"🎯 پردازش تغییرات با اولویت {priority}...")
            for change in changes_by_priority[priority]:
                try:
                    app_name = change['app_name']
                    model_name = change['model_type']
                    model_key = f"{app_name}.{model_name}"

                    if model_key not in model_stats:
                        continue

                    model_class = apps.get_model(app_name, model_name)

                    # پردازش داده‌ها
                    processed_data = self.process_model_data_improved(model_class, change['data'])

                    # مدیریت فیلدهای اجباری
                    processed_data = self.handle_required_fields(model_class, processed_data)

                    if self.validate_required_data(model_class, processed_data):
                        obj, created = model_class.objects.update_or_create(
                            id=change['record_id'],
                            defaults=processed_data
                        )

                        model_stats[model_key]['processed'] += 1
                        total_processed += 1

                        if model_stats[model_key]['processed'] <= 2:
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

                except Exception as e:
                    print(f"  ❌ خطا در پردازش {model_key}: {e}")
                    if model_key in model_stats:
                        model_stats[model_key]['errors'] += 1

        # نمایش گزارش پیشرفته
        self.print_advanced_sync_report(model_stats, total_processed)

        self.last_sync_time = timezone.now()
        return {
            'received_count': total_processed,
            'status': 'success',
            'sync_mode': 'DYNAMIC_AUTO_DISCOVERY',
            'model_stats': model_stats
        }

    def print_advanced_sync_report(self, model_stats, total_processed):
        """چاپ گزارش پیشرفته سینک"""
        print("\n" + "=" * 70)
        print("📊 ﮔﺰارش پیشرفته ﺳیﻨک پویا")
        print("=" * 70)

        # گروه‌بندی بر اساس اولویت
        for priority in ['high', 'medium', 'low']:
            priority_models = {k: v for k, v in model_stats.items() if v.get('priority') == priority}
            if priority_models:
                print(f"\n🎯 اولویت {priority.upper()}:")
                for model_key, stats in priority_models.items():
                    status_icon = "✅" if stats['processed'] == stats['expected'] else "⚠️"
                    print(f"  {status_icon} {model_key}:")
                    print(f"     📈 پردازش شده: {stats['processed']}/{stats['expected']}")
                    if stats['errors'] > 0:
                        print(f"     ❌ خطاها: {stats['errors']}")
                    if stats['skipped'] > 0:
                        print(f"     ⏭️ رد شده: {stats['skipped']}")

        print("\n" + "-" * 70)
        print(f"🎯 کل رکوردهای پردازش شده: {total_processed}")
        print(f"🕒 آخرین بروزرسانی: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🌐 حالت: سینک پویا و خودکار")
        print("=" * 70)
    def discover_local_models(self):
        """کشف خودکار مدل‌های موجود در سیستم محلی"""
        from django.apps import apps

        local_models = {}
        for app_config in apps.get_app_configs():
            app_name = app_config.name
            if any(app_name.startswith(excluded) for excluded in [
                'django.contrib.admin', 'django.contrib.auth',
                'django.contrib.contenttypes', 'django.contrib.sessions'
            ]):
                continue

            for model in app_config.get_models():
                model_key = f"{app_name}.{model.__name__}"
                local_models[model_key] = {
                    'app_name': app_name,
                    'model_name': model.__name__,
                    'model_class': model,
                    'record_count': model.objects.count()
                }

        print(f"🔍 کشف شد: {len(local_models)} مدل در سیستم محلی")
        return local_models

    def ensure_dynamic_default_data(self):
        """ایجاد داده‌های پایه به صورت پویا برای همه مدل‌های ضروری"""
        print("🔄 ایجاد داده‌های پایه پویا...")

        # لیست مدل‌هایی که نیاز به داده پایه دارند
        base_models_config = {
            'cantact_app.Branch': {
                'name': 'شعبه مرکزی',
                'defaults': {'address': 'آدرس پیش‌فرض', 'modem_ip': '192.168.1.1'}
            },
            'dashbord_app.Froshande': {
                'name': 'فروشنده پیش‌فرض',
                'defaults': {'family': 'خانوادگی', 'address': 'آدرس پیش‌فرض'}
            }
        }

        created_count = 0
        for model_key, config in base_models_config.items():
            if model_key in self.discovered_models:
                try:
                    model_class = self.discovered_models[model_key]['model_class']
                    obj, created = model_class.objects.get_or_create(
                        name=config['name'],
                        defaults=config['defaults']
                    )
                    if created:
                        print(f"✅ داده پایه ایجاد شد: {model_key}")
                        created_count += 1
                except Exception as e:
                    print(f"⚠️ خطا در ایجاد داده پایه برای {model_key}: {e}")

        if created_count > 0:
            print(f"🎉 {created_count} داده پایه ایجاد شد")



# ایجاد نمونه سرویس
sync_service = BidirectionalSyncService()


