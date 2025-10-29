from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from account_app.models import Product
from .models import ServerSyncLog, SyncToken
import json


@api_view(['GET'])
@permission_classes([AllowAny])
def sync_pull(request):
    """ارسال داده به کامپیوترهای آفلاین - نسخه ساده‌شده"""
    try:
        print("🔍 شروع sync_pull...")

        # بررسی توکن
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        print(f"📨 هدر احراز: {auth_header}")

        if not auth_header.startswith('Token '):
            return Response({
                'status': 'error',
                'message': 'توکن ارسال نشده است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token_key = auth_header[6:]
        print(f"🔑 توکن دریافت شده: {token_key}")

        # بررسی توکن در دیتابیس
        try:
            token = SyncToken.objects.get(token=token_key, is_active=True)
            print(f"✅ توکن معتبر: {token.name}")
        except SyncToken.DoesNotExist:
            print("❌ توکن نامعتبر")
            return Response({
                'status': 'error',
                'message': 'توکن نامعتبر است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # ایجاد داده تستی ساده
        changes = [
            {
                'model_type': 'product',
                'record_id': 1,
                'action': 'test',
                'data': {
                    'name': 'محصول تستی',
                    'description': 'این یک داده تست است'
                },
                'server_timestamp': timezone.now().isoformat()
            }
        ]

        print(f"📤 ارسال {len(changes)} رکورد")

        return Response({
            'status': 'success',
            'message': 'همگام‌سازی موفق',
            'changes': changes,
            'count': len(changes)
        })

    except Exception as e:
        print(f"❌ خطا در sync_pull: {str(e)}")
        import traceback
        print(traceback.format_exc())

        return Response({
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)