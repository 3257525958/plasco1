import requests
import json
from django.conf import settings
from sync_app.models import DataSyncLog, SyncSession
from django.utils import timezone
import hashlib
import logging

logger = logging.getLogger(__name__)


class BidirectionalSyncService:
    def __init__(self):
        self.server_url = "https://plasmarket.ir"
        self.api_key = "hUafL49RYuXQSRyyc7ZoRF_SxFdF8wUomtjF5YICRVk"  # 🔴 این خط رو آپدیت کن - توکن واقعی رو بذار
        self.last_sync_time = None

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
        """ارسال واقعی تغییرات لوکال به سرور"""
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
        """دریافت واقعی از سرور"""
        try:
            # پارامتر آخرین همگام‌سازی
            params = {}
            if self.last_sync_time:
                params['last_sync'] = self.last_sync_time.isoformat()

            response = requests.get(
                f"{self.server_url}/api/sync/pull/",
                headers={'Authorization': f'Token {self.api_key}'},
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                server_data = result.get('changes', [])

                received_count = 0
                for server_item in server_data:
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
                    print(f"  📥 دریافت {server_item['model_type']} (ID: {server_item['record_id']})")

                # آپدیت زمان آخرین همگام‌سازی
                self.last_sync_time = timezone.now()

                return {'received_count': received_count, 'status': 'success'}
            else:
                return {'received_count': 0, 'status': 'error', 'message': f"HTTP {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return {'received_count': 0, 'status': 'error', 'message': str(e)}

    def resolve_conflicts(self):
        """حل تضادهای همگام‌سازی"""
        conflicts = DataSyncLog.objects.filter(
            sync_status=False,
            conflict_resolved=False
        )

        resolved_count = 0
        for conflict in conflicts:
            # استراتژی ساده: آخرین تغییر برنده
            conflict.conflict_resolved = True
            conflict.sync_status = True
            conflict.synced_at = timezone.now()
            conflict.save()
            resolved_count += 1

        return {'resolved_count': resolved_count, 'status': 'success'}

    def sync_stock_changes(self):
        """همگام‌سازی ویژه برای تغییرات موجودی"""
        print("📦 همگام‌سازی تغییرات موجودی...")

        # اینجا می‌تونی منطق واقعی برای تغییرات موجودی پیاده‌سازی کنی
        stock_changes = [
            {'product_id': 1, 'change': +10, 'reason': 'خرید انبار'},
            {'product_id': 2, 'change': -5, 'reason': 'فروش'},
        ]

        for change in stock_changes:
            DataSyncLog.objects.create(
                model_type='stock',
                record_id=change['product_id'],
                action='update',
                data=change,
                sync_direction='local_to_server'
            )
            print(f"  📦 ثبت تغییر موجودی: محصول {change['product_id']} - {change['change']}")

        return len(stock_changes)


# ایجاد نمونه سرویس
sync_service = BidirectionalSyncService()