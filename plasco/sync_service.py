import requests
import json
from django.conf import settings
from sync_app.models import DataSyncLog, SyncSession
from django.utils import timezone
import hashlib
import logging
import threading
import time

logger = logging.getLogger(__name__)


class BidirectionalSyncService:
    def __init__(self):
        self.server_url = "https://plasmarket.ir"
        self.api_key = "hUafL49RYuXQSRyyc7ZoRF_SxFdF8wUomtjF5YICRVk"  # توکن شما
        self.last_sync_time = None
        self.sync_interval = 60  # 🔥 تغییر به 60 ثانیه (1 دقیقه)
        self.is_running = False

    def start_auto_sync(self):
        """شروع همگام‌سازی خودکار هر 1 دقیقه"""
        if self.is_running:
            print("⚠️ سرویس همگام‌سازی در حال اجراست")
            return

        self.is_running = True
        print(f"🔄 شروع همگام‌سازی خودکار هر {self.sync_interval} ثانیه")

        def sync_worker():
            while self.is_running:
                try:
                    print(f"⏰ همگام‌سازی خودکار در {timezone.now()}")
                    result = self.full_sync_cycle()

                    if result['total_synced'] > 0:
                        print(f"✅ همگام‌سازی موفق: {result['total_synced']} رکورد")
                    else:
                        print("ℹ️ هیچ داده جدیدی برای سینک نبود")

                except Exception as e:
                    print(f"❌ خطا در همگام‌سازی خودکار: {e}")

                # انتظار 1 دقیقه
                time.sleep(self.sync_interval)

        # اجرای در thread جداگانه
        self.sync_thread = threading.Thread(target=sync_worker, daemon=True)
        self.sync_thread.start()

    def stop_auto_sync(self):
        """توقف همگام‌سازی خودکار"""
        self.is_running = False
        print("🛑 همگام‌سازی خودکار متوقف شد")

    def full_sync_cycle(self):
        """یک سیکل کامل همگام‌سازی دوطرفه"""
        print("🔄 شروع سیکل همگام‌سازی دوطرفه...")

        # ایجاد session برای ردیابی
        session = SyncSession.objects.create(
            session_id=f"sync_{int(timezone.now().timestamp())}",
            sync_direction='bidirectional'
        )

        try:
            # ۱. ارسال تغییرات لوکال به سرور
            push_result = self.push_local_changes()
            print(f"📤 ارسال به سرور: {push_result['sent_count']} رکورد")

            # ۲. دریافت تغییرات از سرور
            pull_result = self.pull_server_changes()
            print(f"📥 دریافت از سرور: {pull_result['received_count']} رکورد")

            # ۳. حل تضادها
            conflict_result = self.resolve_conflicts()
            print(f"⚖️ حل تضادها: {conflict_result['resolved_count']} تضاد")

            # آپدیت session
            session.records_synced = push_result['sent_count'] + pull_result['received_count']
            session.status = 'completed'
            session.end_time = timezone.now()
            session.save()

            return {
                'push': push_result,
                'pull': pull_result,
                'conflicts': conflict_result,
                'total_synced': push_result['sent_count'] + pull_result['received_count']
            }

        except Exception as e:
            session.status = 'failed'
            session.end_time = timezone.now()
            session.save()
            logger.error(f"خطا در همگام‌سازی: {e}")
            return {
                'push': {'sent_count': 0, 'status': 'error'},
                'pull': {'received_count': 0, 'status': 'error'},
                'conflicts': {'resolved_count': 0, 'status': 'error'},
                'total_synced': 0
            }

    def push_local_changes(self):
        """ارسال تغییرات لوکال به سرور"""
        # کد فعلی شما بدون تغییر
        unsynced_logs = DataSyncLog.objects.filter(
            sync_status=False,
            sync_direction='local_to_server'
        )

        sent_count = 0
        for log in unsynced_logs:
            try:
                # ارسال واقعی به API سرور
                response = requests.post(
                    f"{self.server_url}/api/sync/push/",
                    json={
                        'model_type': log.model_type,
                        'record_id': log.record_id,
                        'action': log.action,
                        'data': log.data
                    },
                    headers={'Authorization': f'Token {self.api_key}'},
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    if result['status'] == 'success':
                        log.sync_status = True
                        log.synced_at = timezone.now()
                        log.save()
                        sent_count += 1
                        print(f"  ✅ ارسال موفق {log.model_type} (ID: {log.record_id})")
                    else:
                        print(f"  ❌ خطا از سرور: {result['message']}")
                        log.error_message = result['message']
                        log.save()
                else:
                    print(f"  ❌ خطای HTTP: {response.status_code}")
                    log.error_message = f"HTTP {response.status_code}"
                    log.save()

            except requests.exceptions.RequestException as e:
                print(f"  ❌ خطای ارتباط: {e}")
                log.error_message = str(e)
                log.save()

        return {'sent_count': sent_count, 'status': 'success'}

    def pull_server_changes(self):
        """دریافت از سرور و ذخیره در مدل‌های واقعی"""
        try:
            response = requests.get(
                f"{self.server_url}/api/sync/pull/",
                headers={'Authorization': f'Token {self.api_key}'},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                server_data = result.get('changes', [])

                received_count = 0
                for server_item in server_data:
                    # 🔥 ذخیره در مدل‌های واقعی
                    if server_item['model_type'] == 'product':
                        from account_app.models import Product
                        Product.objects.update_or_create(
                            id=server_item['record_id'],
                            defaults=server_item['data']
                        )
                        print(f"  📦 محصول: {server_item['data']['name']}")

                    elif server_item['model_type'] == 'contact':
                        from cantact_app.models import Contact
                        Contact.objects.update_or_create(
                            id=server_item['record_id'],
                            defaults=server_item['data']
                        )
                        print(f"  👥 مخاطب: {server_item['data']['name']}")

                    elif server_item['model_type'] == 'invoice':
                        from invoice_app.models import Invoice
                        Invoice.objects.update_or_create(
                            id=server_item['record_id'],
                            defaults=server_item['data']
                        )
                        print(f"  🧾 فاکتور: {server_item['data']['invoice_number']}")

                    # همچنین در لاگ هم ذخیره شود
                    DataSyncLog.objects.create(
                        model_type=server_item['model_type'],
                        record_id=server_item['record_id'],
                        action=server_item['action'],
                        data=server_item['data'],
                        sync_direction='server_to_local',
                        sync_status=True,
                        synced_at=timezone.now()
                    )
                    received_count += 1

                self.last_sync_time = timezone.now()
                return {'received_count': received_count, 'status': 'success'}
            else:
                return {'received_count': 0, 'status': 'error', 'message': f"HTTP {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return {'received_count': 0, 'status': 'error', 'message': str(e)}
    def resolve_conflicts(self):
        """حل تضادها"""
        # کد فعلی شما بدون تغییر
        conflicts = DataSyncLog.objects.filter(
            sync_status=False,
            conflict_resolved=False
        )

        resolved_count = 0
        for conflict in conflicts:
            conflict.conflict_resolved = True
            conflict.sync_status = True
            conflict.synced_at = timezone.now()
            conflict.save()
            resolved_count += 1

        return {'resolved_count': resolved_count, 'status': 'success'}


# ایجاد نمونه سرویس
sync_service = BidirectionalSyncService()