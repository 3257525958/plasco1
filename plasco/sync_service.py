import requests
import json
from django.conf import settings
from sync_app.models import DataSyncLog
from django.utils import timezone
from django.apps import apps


class UniversalSyncService:
    def __init__(self):
        self.server_url = "https://plasmarket.ir"
        self.sync_models = self.discover_all_models()
        print(f"🔍 کشف شد: {len(self.sync_models)} مدل برای سینک")

    def discover_all_models(self):
        """کشف خودکار مدل‌ها"""
        sync_models = {}

        for app_config in apps.get_app_configs():
            app_name = app_config.name
            if any(app_name.startswith(excluded) for excluded in [
                'django.contrib.admin', 'django.contrib.auth',
                'django.contrib.contenttypes', 'django.contrib.sessions'
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

                # ایجاد یا آپدیت رکورد در دیتابیس محلی
                # فیلتر کردن فیلدهایی که در مدل وجود دارند
                try:
                    model_fields = [f.name for f in model_class._meta.get_fields()]
                    filtered_data = {}

                    for field_name, value in data.items():
                        if field_name in model_fields:
                            filtered_data[field_name] = value
                        else:
                            print(f"⚠️ فیلد ناشناخته {field_name} در {model_key} نادیده گرفته شد")

                    if filtered_data:  # فقط اگر فیلد معتبر وجود دارد
                        obj, created = model_class.objects.update_or_create(
                            id=record_id,
                            defaults=filtered_data
                        )

                        processed_count += 1
                        if processed_count <= 10:  # فقط 10 تای اول را لاگ کن
                            action = "ایجاد" if created else "آپدیت"
                            print(f"✅ {action}: {model_key} - ID: {record_id}")
                    else:
                        print(f"⚠️ هیچ فیلد معتبری برای {model_key} - ID: {record_id}")
                        continue

                except Exception as e:
                    print(f"❌ خطا در پردازش {model_key}: {e}")
                    continue







                processed_count += 1
                if processed_count <= 10:  # فقط 10 تای اول را لاگ کن
                    action = "ایجاد" if created else "آپدیت"
                    print(f"✅ {action}: {model_key} - ID: {record_id}")

            except Exception as e:
                print(f"❌ خطا در پردازش {model_key}: {e}")
                continue

        print(f"🎯 دریافت شد: {processed_count} رکورد از سرور اصلی")
        return {'status': 'success', 'processed_count': processed_count}

    def upload_to_server(self):
        """ارسال تغییرات محلی به سرور اصلی"""
        if not settings.OFFLINE_MODE:
            return 0

        print("📤 ارسال تغییرات به سرور اصلی...")
        unsynced = DataSyncLog.objects.filter(sync_status=False)
        sent_count = 0

        for log in unsynced:
            try:
                # پیدا کردن مدل مربوطه
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

        # 1. اول تغییرات محلی را به سرور ارسال کن
        sent = self.upload_to_server()

        # 2. سپس داده‌های جدید را از سرور دریافت کن
        download_result = self.download_from_server()
        received = download_result.get('processed_count', 0)

        return {
            'sent_to_server': sent,
            'received_from_server': received,
            'total': sent + received
        }


# ایجاد سرویس
sync_service = UniversalSyncService()
