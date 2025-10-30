from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.apps import apps
from .models import SyncToken
from .sync_config import SYNC_CONFIG
import json


@api_view(['GET'])
def sync_pull(request):
    """ارسال همه داده‌ها به کامپیوترهای آفلاین"""
    try:
        print("🔄 درخواست sync_pull برای همه مدل‌ها دریافت شد")

        # بررسی توکن
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Token '):
            return Response({
                'status': 'error',
                'message': 'توکن ارسال نشده است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token_key = auth_header[6:]

        try:
            token = SyncToken.objects.get(token=token_key, is_active=True)
            print(f"✅ توکن معتبر: {token.name}")
        except SyncToken.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'توکن نامعتبر است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        changes = []
        total_records = 0

        # 🔥 سینک همه مدل‌ها بر اساس config
        for app_name, models in SYNC_CONFIG.items():
            for model_name, config in models.items():
                try:
                    # گرفتن مدل
                    model_class = apps.get_model(app_name, model_name)

                    # گرفتن همه رکوردها
                    records = model_class.objects.all()[:config['batch_size']]

                    for record in records:
                        # ساخت دیتا
                        record_data = {}
                        for field in config['fields']:
                            if hasattr(record, field):
                                value = getattr(record, field)
                                # تبدیل انواع مختلف به string
                                if hasattr(value, 'isoformat'):  # برای DateTime
                                    record_data[field] = value.isoformat()
                                else:
                                    record_data[field] = str(value) if value is not None else ''

                        changes.append({
                            'app_name': app_name,
                            'model_type': model_name,
                            'record_id': record.id,
                            'action': 'create_or_update',
                            'data': record_data,
                            'server_timestamp': timezone.now().isoformat()
                        })

                        total_records += 1

                    print(f"✅ {app_name}.{model_name}: {len(records)} رکورد")

                except Exception as e:
                    print(f"⚠️ خطا در مدل {app_name}.{model_name}: {e}")
                    continue

        print(f"📤 ارسال {total_records} رکورد از {len(changes)} مدل")

        return Response({
            'status': 'success',
            'message': f'همگام‌سازی {total_records} رکورد موفق',
            'changes': changes,
            'total_records': total_records
        })

    except Exception as e:
        print(f"❌ خطا در sync_pull: {str(e)}")
        import traceback
        traceback.print_exc()

        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)