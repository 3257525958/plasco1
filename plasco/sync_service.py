import requests
import json
import time
import decimal
import threading
from decimal import Decimal
from django.db import models
from django.conf import settings
# from sync_app.models import DataSyncLog  # این خط را کامنت کنید موقتاً
from sync_app.models import DataSyncLog
from django.utils import timezone
from django.apps import apps


class UniversalSyncService:
    def __init__(self):
        self.server_url = "https://plasmarket.ir"
        self.sync_models = self.discover_all_models()
        self.is_running = False
        print(f"🔍 کشف شد: {len(self.sync_models)} مدل برای سینک")

    def start_auto_sync(self):
        """شروع سینک خودکار در فواصل زمانی"""
        if self.is_running:
            return

        self.is_running = True
        print("🔄 سرویس سینک خودکار فعال شد")

        def sync_loop():
            while self.is_running:
                try:
                    print("⏰ شروع سینک دوره‌ای...")
                    result = self.full_sync()
                    print(f"✅ سینک دوره‌ای انجام شد: {result}")
                except Exception as e:
                    print(f"❌ خطا در سینک دوره‌ای: {e}")

                time.sleep(600)

        threading.Thread(target=sync_loop, daemon=True).start()

    def stop_auto_sync(self):
        """توقف سرویس سینک"""
        self.is_running = False
        print("🛑 سرویس سینک خودکار متوقف شد")

    def discover_all_models(self):
        """کشف خودکار تمام مدل‌های موجود در پروژه"""
        sync_models = {}

        for app_config in apps.get_app_configs():
            app_name = app_config.name
            if any(app_name.startswith(excluded) for excluded in [
                'django.contrib.admin', 'django.contrib.auth',
                'django.contrib.contenttypes', 'django.contrib.sessions',
                'django.contrib.messages', 'django.contrib.staticfiles',
                'sync_app', 'sync_api'
            ]):
                continue

            for model in app_config.get_models():
                model_name = model.__name__
                model_key = f"{app_name}.{model_name}"

                if model_name in ['DataSyncLog', 'SyncSession', 'OfflineSetting', 'ServerSyncLog', 'SyncToken']:
                    continue

                sync_models[model_key] = {
                    'app_name': app_name,
                    'model_name': model_name,
                    'model_class': model
                }

        return sync_models

    def download_from_server(self):
        """دریافت تمام داده‌ها از سرور اصلی"""
        print("📥 دریافت داده از سرور اصلی...")

        try:
            response = requests.get(f"{self.server_url}/api/sync/pull/", timeout=60)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return self.process_server_data(data)
                else:
                    return {'status': 'error', 'message': data.get('message', 'خطا در سرور')}
            else:
                return {'status': 'error', 'message': f'خطا در ارتباط: {response.status_code}'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def process_server_data(self, payload):
        """پردازش داده‌های دریافتی از سرور اصلی"""
        processed_count = 0
        errors = []

        for change in payload.get('changes', []):
            try:
                app_name = change['app_name']
                model_name = change['model_type']
                model_key = f"{app_name}.{model_name}"

                if model_key not in self.sync_models:
                    print(f"⚠️ مدل ناشناخته: {model_key}")
                    continue

                model_class = self.sync_models[model_key]['model_class']
                record_id = change['record_id']
                data = change['data']

                filtered_data = self._filter_and_convert_data(model_class, data, model_key)

                if not filtered_data:
                    print(f"⚠️ هیچ فیلد معتبری برای {model_key} - ID: {record_id}")
                    continue

                obj, created = model_class.objects.update_or_create(
                    id=record_id,
                    defaults=filtered_data
                )

                processed_count += 1
                if processed_count <= 10:
                    action = "ایجاد" if created else "آپدیت"
                    print(f"✅ {action}: {model_key} - ID: {record_id}")

            except Exception as e:
                error_msg = f"❌ خطا در پردازش {model_key} - ID {record_id}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                continue

        print(f"🎯 دریافت شد: {processed_count} رکورد از سرور اصلی")
        if errors:
            print(f"⚠️ {len(errors)} خطا در پردازش")

        return {
            'status': 'success',
            'processed_count': processed_count,
            'errors': errors
        }

    def _filter_and_convert_data(self, model_class, data, model_key):
        """فیلتر و تبدیل داده‌ها به انواع صحیح"""
        filtered_data = {}

        try:
            model_fields = {}
            for field in model_class._meta.get_fields():
                if not field.is_relation or (field.is_relation and not field.auto_created):
                    model_fields[field.name] = field

            for field_name, value in data.items():
                if field_name not in model_fields:
                    continue

                field = model_fields[field_name]

                if value in ["None", "null", None, ""]:
                    continue

                try:
                    if hasattr(field, 'get_internal_type'):
                        field_type = field.get_internal_type()

                        if field_type in ['DecimalField', 'FloatField']:
                            try:
                                filtered_data[field_name] = float(value)
                            except (ValueError, TypeError):
                                filtered_data[field_name] = value

                        elif field_type == 'IntegerField':
                            try:
                                filtered_data[field_name] = int(value)
                            except (ValueError, TypeError):
                                filtered_data[field_name] = value

                        elif field_type == 'BooleanField':
                            if isinstance(value, str):
                                filtered_data[field_name] = value.lower() in ['true', '1', 'yes', 'y']
                            else:
                                filtered_data[field_name] = bool(value)
                        else:
                            filtered_data[field_name] = value
                    else:
                        filtered_data[field_name] = value

                except (ValueError, TypeError) as e:
                    print(f"⚠️ خطا در تبدیل فیلد {field_name}: {value} -> {e}")
                    filtered_data[field_name] = value
                    continue

        except Exception as e:
            print(f"⚠️ خطا در فیلتر داده‌ها: {e}")
            for field_name, value in data.items():
                if value not in ["None", "null", None, ""]:
                    filtered_data[field_name] = value

        filtered_data = self._handle_required_fields(model_key, filtered_data)
        return filtered_data

    def _handle_required_fields(self, model_key, data):
        """مدیریت فیلدهای اجباری برای مدل‌های خاص"""
        # برای InventoryCount
        if model_key == 'account_app.InventoryCount':
            if 'branch_id' not in data:
                try:
                    from cantact_app.models import Branch
                    default_branch = Branch.objects.first()
                    if default_branch:
                        data['branch_id'] = default_branch.id
                        print(f"✅ branch_id پیش‌فرض برای InventoryCount اضافه شد: {default_branch.id}")
                except Exception as e:
                    print(f"⚠️ خطا در دریافت شعبه پیش‌فرض برای InventoryCount: {e}")

        # برای Invoicefrosh
        elif model_key == 'invoice_app.Invoicefrosh':
            if 'branch_id' not in data:
                try:
                    from cantact_app.models import Branch
                    default_branch = Branch.objects.first()
                    if default_branch:
                        data['branch_id'] = default_branch.id
                except Exception as e:
                    print(f"⚠️ خطا در دریافت شعبه پیش‌فرض: {e}")

            if 'created_by_id' not in data:
                try:
                    from django.contrib.auth.models import User
                    default_user = User.objects.first()
                    if default_user:
                        data['created_by_id'] = default_user.id
                except Exception as e:
                    print(f"⚠️ خطا در دریافت کاربر پیش‌فرض: {e}")

        # برای Expense
        elif model_key == 'account_app.Expense':
            if 'branch_id' not in data:
                try:
                    from cantact_app.models import Branch
                    default_branch = Branch.objects.first()
                    if default_branch:
                        data['branch_id'] = default_branch.id
                except Exception as e:
                    print(f"⚠️ خطا در دریافت شعبه پیش‌فرض برای Expense: {e}")

            if 'user_id' not in data:
                try:
                    from django.contrib.auth.models import User
                    default_user = User.objects.first()
                    if default_user:
                        data['user_id'] = default_user.id
                except Exception as e:
                    print(f"⚠️ خطا در دریافت کاربر پیش‌فرض برای Expense: {e}")

        return data

    def upload_to_server(self):
        """ارسال تغییرات محلی به سرور اصلی"""
        if not settings.OFFLINE_MODE:
            return 0

        # import داخلی برای جلوگیری از circular import
        from sync_app.models import DataSyncLog

        print("📤 ارسال تغییرات به سرور اصلی...")
        unsynced = DataSyncLog.objects.filter(sync_status=False)
        sent_count = 0

        for log in unsynced:
            try:
                model_key = f"{log.model_type}"
                if model_key in self.sync_models:
                    app_name = self.sync_models[model_key]['app_name']
                else:
                    app_name = 'unknown'

                sync_data = {
                    'app_name': app_name,
                    'model_type': log.model_type,
                    'record_id': log.record_id,
                    'action': log.action,
                    'data': log.data,
                    'created_at': log.created_at.isoformat()
                }

                response = requests.post(
                    f"{self.server_url}/api/sync/receive/",
                    json=sync_data,
                    timeout=30
                )

                if response.status_code == 200:
                    log.sync_status = True
                    log.synced_at = timezone.now()
                    log.save()
                    sent_count += 1
                    print(f"✅ ارسال شد: {log.model_type} - ID: {log.record_id}")

            except Exception as e:
                print(f"❌ خطا در ارسال: {e}")
                continue

        return sent_count

    def full_sync(self):
        """سینک کامل: دریافت از سرور + ارسال تغییرات"""
        print("🔄 شروع سینک کامل با سرور اصلی...")

        sent = self.upload_to_server()
        download_result = self.download_from_server()
        received = download_result.get('processed_count', 0)

        return {
            'sent_to_server': sent,
            'received_from_server': received,
            'total': sent + received
        }


# ایجاد سرویس جهانی
sync_service = UniversalSyncService()