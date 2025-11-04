# sync_service.py
import requests
import json
import time
import decimal
import threading
from decimal import Decimal
from django.db import models
from django.conf import settings
from sync_app.models import DataSyncLog
from django.utils import timezone
from django.apps import apps


class UniversalSyncService:
    def __init__(self):
        print("🔄 راه‌اندازی سرویس سینک جهانی...")

        # ابتدا تمام متغیرهای ضروری را تعریف می‌کنیم
        self.server_url = getattr(settings, 'ONLINE_SERVER_URL', 'https://plasmarket.ir')
        self.online_url = self.server_url
        self.offline_mode = getattr(settings, 'OFFLINE_MODE', False)
        self.is_running = False
        self.sync_models = self.discover_all_models()  # این خط مهم است!

        print(f"🔍 کشف شد: {len(self.sync_models)} مدل برای سینک")
        print(f"🌐 آدرس سرور: {self.server_url}")

        # بررسی تنظیمات قبل از شروع سینک خودکار
        if not getattr(settings, 'SYNC_AUTO_START', True):
            print("🔴 سرویس سینک خودکار غیرفعال شده (از طریق settings)")
            return


        self.sync_models = self.discover_all_models()
        print(f"🔍 کشف شد: {len(self.sync_models)} مدل برای سینک")
        # تعریف هر دو آدرس برای سازگاری
        self.server_url = getattr(settings, 'ONLINE_SERVER_URL', 'https://plasmarket.ir')
        self.online_url = self.server_url  # برای سازگاری با کد موجود
        self.offline_mode = getattr(settings, 'OFFLINE_MODE', False)
        self.sync_models = self.discover_all_models()
        self.is_running = False
        print(f"🔍 کشف شد: {len(self.sync_models)} مدل برای سینک")
        print(f"🌐 آدرس سرور: {self.server_url}")

    def start_auto_sync(self):
        """شروع سینک خودکار در فواصل زمانی"""
        # بررسی تنظیمات قبل از شروع
        if not getattr(settings, 'SYNC_AUTO_START', True):
            print("🔴 سرویس سینک خودکار غیرفعال شده")
            return

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

                time.sleep(600)  # 10 دقیقه

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

    def check_internet_connection(self):
        """بررسی اتصال به اینترنت"""
        try:
            response = requests.get(f"{self.server_url}/", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ عدم اتصال به سرور: {e}")
            return False

    def download_from_server(self):
        """دریافت تمام داده‌ها از سرور اصلی"""
        print("📥 دریافت داده از سرور اصلی...")

        try:
            # بررسی اتصال اینترنت
            if not self.check_internet_connection():
                return {'status': 'error', 'message': 'اتصال به سرور میسر نیست'}

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
                if processed_count <= 10:  # فقط 10 تا اول را نمایش بده
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
            # در صورت خطا، تمام داده‌ها را بدون فیلتر کردن بریز
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

    def sync_specific_app(self, app_name):
        """سینک فقط یک اپ خاص"""
        print(f"🎯 شروع سینک مدل‌های {app_name} از سرور به لوکال...")

        # بررسی اتصال
        print("🔗 تست اتصال به سرور...")
        if not self.check_internet_connection():
            print("❌ اتصال به سرور برقرار نیست")
            return {'status': 'error', 'message': 'اتصال به سرور برقرار نیست'}

        try:
            response = requests.get(f"{self.server_url}/api/sync/pull/", timeout=60)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return self.process_specific_app_data(data, app_name)
                else:
                    return {'status': 'error', 'message': data.get('message', 'خطا در سرور')}
            else:
                return {'status': 'error', 'message': f'خطا در ارتباط: {response.status_code}'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def process_specific_app_data(self, payload, target_app):
        """پردازش داده‌های یک اپ خاص"""
        changes = payload.get('changes', [])
        app_changes = [ch for ch in changes if ch.get('app_name') == target_app]

        processed_count = 0
        errors = []

        print(f"📥 دریافت {len(app_changes)} رکورد از {target_app}")

        for change in app_changes:
            try:
                app_name = change['app_name']
                model_name = change['model_type']
                record_id = change['record_id']  # این خط باید قبل از استفاده باشد
                model_key = f"{app_name}.{model_name}"

                if model_key not in self.sync_models:
                    print(f"⚠️ مدل ناشناخته: {model_key}")
                    continue

                model_class = self.sync_models[model_key]['model_class']
                data = change['data']

                # فیلتر و تبدیل داده‌ها
                filtered_data = {}
                for field_name, value in data.items():
                    if value not in ["None", "null", None, ""]:
                        filtered_data[field_name] = value

                if not filtered_data:
                    print(f"⚠️ هیچ فیلد معتبری برای {model_key} - ID: {record_id}")
                    continue

                obj, created = model_class.objects.update_or_create(
                    id=record_id,
                    defaults=filtered_data
                )

                processed_count += 1
                action = "ایجاد" if created else "آپدیت"
                print(f"✅ {action}: {model_key} - ID: {record_id}")

            except Exception as e:
                # استفاده از record_id از scope بیرونی
                record_id = change.get('record_id', 'نامشخص')
                model_key = f"{change.get('app_name', 'نامشخص')}.{change.get('model_type', 'نامشخص')}"
                error_msg = f"❌ خطا در پردازش {model_key} - ID {record_id}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                continue

        print(f"🎯 سینک {target_app} کامل شد: {processed_count} رکورد پردازش شد")
        if errors:
            print(f"⚠️ {len(errors)} خطا در پردازش")

        return {
            'status': 'success',
            'app_name': target_app,
            'processed_count': processed_count,
            'errors': errors
        }


    def sync_incremental(self, app_name, last_sync_time=None):
        """سینک افزایشی - فقط داده‌های تغییر کرده پس از زمان مشخص"""
        print(f"🔄 سینک افزایشی {app_name} از زمان {last_sync_time}...")

        if not self.check_internet_connection():
            return {'status': 'error', 'message': 'اتصال به سرور میسر نیست'}

        try:
            # پارامتر زمان برای سینک افزایشی
            params = {}
            if last_sync_time:
                params['last_sync'] = last_sync_time.isoformat()

            response = requests.get(
                f"{self.server_url}/api/sync/pull/",
                params=params,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return self.process_specific_app_data(data, app_name)
                else:
                    return {'status': 'error', 'message': data.get('message', 'خطا در سرور')}
            else:
                return {'status': 'error', 'message': f'خطا در ارتباط: {response.status_code}'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_all_models_for_app(self, app_name):
        """
        دریافت تمام مدل‌های یک زیربرنامه
        """
        try:
            from django.apps import apps

            models_list = []
            app_config = apps.get_app_config(app_name)

            for model in app_config.get_models():
                model_info = {
                    'app_name': app_name,
                    'model_name': model.__name__,
                    'model_class': model,
                    'fields': [f.name for f in model._meta.get_fields()],
                    'record_count': model.objects.count()
                }
                models_list.append(model_info)

            print(f"✅ پیدا شد {len(models_list)} مدل در {app_name}")
            return models_list

        except LookupError:
            print(f"❌ زیربرنامه {app_name} پیدا نشد")
            return []
        except Exception as e:
            print(f"❌ خطا در دریافت مدل‌های {app_name}: {e}")
            return []

    def check_previous_sync(self, app_name, models_list):
        """
        بررسی اینکه آیا مدل‌های یک زیربرنامه قبلاً سینک شده‌اند یا نه
        """
        try:
            from sync_app.models import DataSyncLog

            sync_status = {}

            for model_info in models_list:
                model_name = model_info['model_name']

                # بررسی آخرین سینک موفق
                last_sync = DataSyncLog.objects.filter(
                    app_name=app_name,
                    model_name=model_name,
                    sync_status=True
                ).order_by('-synced_at').first()

                if last_sync:
                    sync_status[model_name] = {
                        'is_synced': True,
                        'last_sync_time': last_sync.synced_at,
                        'last_sync_id': last_sync.record_id,
                        'sync_count': DataSyncLog.objects.filter(
                            app_name=app_name,
                            model_name=model_name,
                            sync_status=True
                        ).count()
                    }
                else:
                    sync_status[model_name] = {
                        'is_synced': False,
                        'last_sync_time': None,
                        'last_sync_id': 0,
                        'sync_count': 0
                    }

            return sync_status

        except Exception as e:
            print(f"❌ خطا در بررسی سینک قبلی: {e}")
            return {}
# ایجاد سرویس جهانی
sync_service = UniversalSyncService()

# غیرفعال کردن شروع خودکار سرویس
if not getattr(settings, 'SYNC_AUTO_START', True):
    print("🔴 سرویس سینک خودکار غیرفعال شده (در سطح ماژول)")
    sync_service.is_running = False

