# sync_api/views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import SyncToken
from .auto_sync import SmartSyncEngine


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def sync_pull(request):
    """سینک هوشمند پویا - کشف خودکار همه مدل‌ها"""
    try:
        print("🤖 راه‌اندازی موتور سینک پویا...")

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

        # ایجاد موتور سینک پویا
        sync_engine = SmartSyncEngine()

        # تولید پکیج سینک پویا
        sync_payload = sync_engine.generate_dynamic_sync_payload()

        return Response({
            'status': 'success',
            'message': f'سینک پویا - {sync_payload["summary"]["total_records"]} رکورد از {sync_payload["summary"]["total_models"]} مدل',
            'sync_mode': 'DYNAMIC_AUTO_DISCOVERY',
            'payload': sync_payload
        })

    except Exception as e:
        print(f"❌ خطا در سینک پویا: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'status': 'error',
            'message': f'خطا در سینک پویا: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)