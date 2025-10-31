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
        """کشف خودکار تمام مدل‌های پروژه"""
        sync_models = {}

        for app_config in apps.get_app_configs():
            app_name = app_config.name
            # نادیده گرفتن اپ‌های سیستمی
            if any(app_name.startswith(excluded) for excluded in [
                'django.contrib.admin', 'django.contrib.auth',
                'django.contrib.contenttypes', 'django.contrib.sessions'
            ]):
                continue

            for model in app_config.get_models():
                model_name = model.__name__
                model_key = f"{app_name}.{model_name}"

                # نادیده گرفتن مدل‌های سینک
                if model_name in ['DataSyncLog', 'SyncSession', 'OfflineSetting', 'ServerSyncLog', 'SyncToken']:
                    continue

                sync_models[model_key] = {
                    'app_name': app_name,
                    'model_name': model_name,
                    'model_class': model
                }

        return sync_models

    def push_to_server(self):
        """ارسال تغییرات محلی به سرور"""
        if not settings.OFFLINE_MODE:
            print("🟢 در حالت آنلاین - نیازی به ارسال نیست")
            return 0

        print("📤 ارسال تغییرات به سرور...")
        unsynced = DataSyncLog.objects.filter(sync_status=False)
        sent_count = 0

        for log in unsynced:
            try:
                sync_data = {
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

    def pull_from_server(self):
        """دریافت تغییرات از سرور"""
        print("📥 دریافت تغییرات از سرور...")

        try:
            response = requests.get(f"{self.server_url}/api/sync/pull/", timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self.process_server_data(data)
            else:
                return {'status': 'error', 'message': 'خطا در ارتباط'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def process_server_data(self, payload):
        """پردازش داده‌های دریافتی از سرور"""
        processed_count = 0

        for change in payload.get('changes', []):
            try:
                app_name = change['app_name']
                model_name = change['model_type']
                model_key = f"{app_name}.{model_name}"

                if model_key not in self.sync_models:
                    continue

                model_class = self.sync_models[model_key]['model_class']
                record_id = change['record_id']
                data = change['data']

                # ایجاد یا آپدیت رکورد
                obj, created = model_class.objects.update_or_create(
                    id=record_id,
                    defaults=data
                )

                processed_count += 1
                action = "ایجاد" if created else "آپدیت"
                print(f"✅ {action}: {model_key} - ID: {record_id}")

            except Exception as e:
                print(f"❌ خطا در پردازش: {e}")
                continue

        return {'status': 'success', 'processed_count': processed_count}

    def full_sync(self):
        """سینک کامل دوطرفه"""
        print("🔄 شروع سینک دوطرفه...")

        # فقط در آفلاین به سرور ارسال کن
        if settings.OFFLINE_MODE:
            sent = self.push_to_server()
        else:
            sent = 0

        # از سرور دریافت کن (هم در آفلاین هم آنلاین)
        pull_result = self.pull_from_server()
        received = pull_result.get('processed_count', 0)

        return {
            'sent_to_server': sent,
            'received_from_server': received,
            'total': sent + received
        }


# ایجاد سرویس
sync_service = UniversalSyncService()