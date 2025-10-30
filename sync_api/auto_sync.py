# sync_api/auto_sync.py
from django.apps import apps
from django.db import models
from django.utils import timezone
from django.core.exceptions import FieldDoesNotExist
import json


class SmartSyncEngine:
    def __init__(self):
        # مدل‌هایی که نباید سینک شوند
        self.excluded_models = [
            'ContentType', 'Session', 'LogEntry', 'Permission', 'Group',
            'Migration', 'Token', 'DataSyncLog', 'ServerSyncLog',
            'SyncToken', 'SyncSession', 'TokenProxy'
        ]

        # اپ‌هایی که نباید سینک شوند
        self.excluded_apps = [
            'django.contrib.admin', 'django.contrib.auth',
            'django.contrib.contenttypes', 'django.contrib.sessions',
            'django.contrib.messages', 'django.contrib.staticfiles',
            'rest_framework', 'rest_framework.authtoken', 'corsheaders'
        ]

    def discover_all_models(self):
        """کشف خودکار همه مدل‌های قابل سینک"""
        print("🔍 در حال کشف خودکار همه مدل‌ها...")

        syncable_models = []

        for app_config in apps.get_app_configs():
            app_name = app_config.name

            # نادیده گرفتن اپ‌های سیستمی
            if any(app_name.startswith(excluded) for excluded in self.excluded_apps):
                continue

            print(f"📁 بررسی اپ: {app_name}")

            for model in app_config.get_models():
                model_name = model.__name__

                # نادیده گرفتن مدل‌های سیستمی
                if model_name in self.excluded_models:
                    continue

                model_info = {
                    'app_name': app_name,
                    'model_name': model_name,
                    'model_class': model,
                    'fields': self.analyze_model_fields(model),
                    'record_count': model.objects.count()
                }

                syncable_models.append(model_info)
                print(f"  ✅ پیدا شد: {model_name} ({model_info['record_count']} رکورد)")

        print(f"🎯 تعداد مدل‌های قابل سینک: {len(syncable_models)}")
        return syncable_models

    def analyze_model_fields(self, model_class):
        """آنالیز هوشمند فیلدهای مدل"""
        fields_info = []

        for field in model_class._meta.get_fields():
            field_info = {
                'name': field.name,
                'type': type(field).__name__,
                'is_relation': field.is_relation,
                'editable': getattr(field, 'editable', True),
                'nullable': getattr(field, 'null', False)
            }

            # برای فیلدهای رابطه‌ای
            if field.is_relation and field.related_model:
                field_info['related_model'] = {
                    'app': field.related_model._meta.app_label,
                    'model': field.related_model.__name__
                }

            fields_info.append(field_info)

        return fields_info

    def serialize_model_data(self, model_class, batch_size=200):
        """سریالایز کردن هوشمند داده‌های مدل"""
        try:
            records = model_class.objects.all()[:batch_size]
            serialized_records = []

            for record in records:
                record_data = {}

                for field in model_class._meta.get_fields():
                    # فقط فیلدهای ساده و غیر-رابطه‌ای را پردازش کن
                    if field.is_relation and not field.one_to_one:
                        continue

                    field_name = field.name

                    try:
                        value = getattr(record, field_name)

                        # تبدیل هوشمند انواع داده
                        if value is None:
                            record_data[field_name] = None
                        elif hasattr(value, 'isoformat'):  # DateTime/Date
                            record_data[field_name] = value.isoformat()
                        elif isinstance(value, (int, float)):
                            record_data[field_name] = value
                        elif isinstance(value, bool):
                            record_data[field_name] = value
                        else:
                            record_data[field_name] = str(value)

                    except (AttributeError, ValueError) as e:
                        record_data[field_name] = None

                serialized_records.append({
                    'id': record.id,
                    'data': record_data,
                    'timestamp': timezone.now().isoformat()
                })

            return serialized_records

        except Exception as e:
            print(f"❌ خطا در سریالایز مدل {model_class.__name__}: {e}")
            return []

    def generate_sync_payload(self):
        """تولید پکیج کامل سینک"""
        all_models = self.discover_all_models()
        sync_payload = {
            'models': [],
            'changes': [],
            'summary': {
                'total_models': 0,
                'total_records': 0,
                'generated_at': timezone.now().isoformat()
            }
        }

        total_records = 0

        for model_info in all_models:
            model_class = model_info['model_class']
            app_name = model_info['app_name']
            model_name = model_info['model_name']

            # سریالایز کردن داده‌های مدل
            model_data = self.serialize_model_data(model_class)

            if model_data:
                # اضافه کردن به لیست مدل‌ها
                sync_payload['models'].append({
                    'app': app_name,
                    'model': model_name,
                    'fields': model_info['fields'],
                    'record_count': len(model_data)
                })

                # اضافه کردن داده‌ها
                for data_item in model_data:
                    sync_payload['changes'].append({
                        'app_name': app_name,
                        'model_type': model_name,
                        'record_id': data_item['id'],
                        'action': 'auto_sync',
                        'data': data_item['data'],
                        'server_timestamp': data_item['timestamp']
                    })

                total_records += len(model_data)
                print(f"📦 {app_name}.{model_name}: {len(model_data)} رکورد آماده")

        sync_payload['summary']['total_models'] = len(sync_payload['models'])
        sync_payload['summary']['total_records'] = total_records

        print(f"🎉 پکیج سینک تولید شد: {len(sync_payload['models'])} مدل, {total_records} رکورد")
        return sync_payload