from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import SyncToken


@api_view(['GET'])
@authentication_classes([])  # 🔥 غیرفعال کردن authentication پیشفرض
@permission_classes([])  # 🔥 غیرفعال کردن permission پیشفرض
def sync_pull(request):
    """ارسال داده به کامپیوترهای آفلاین"""
    try:
        # بررسی توکن دستی
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Token '):
            return Response({
                'status': 'error',
                'message': 'توکن ارسال نشده است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token_key = auth_header[6:]

        # بررسی توکن در دیتابیس
        try:
            token = SyncToken.objects.get(token=token_key, is_active=True)
            print(f"✅ توکن معتبر: {token.name}")
        except SyncToken.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'توکن نامعتبر است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # داده تستی
        changes = [
            {
                'model_type': 'test',
                'record_id': 1,
                'action': 'test',
                'data': {'name': 'داده تستی از سرور'},
                'server_timestamp': timezone.now().isoformat()
            }
        ]

        return Response({
            'status': 'success',
            'message': 'همگام‌سازی موفق',
            'changes': changes,
            'count': len(changes)
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)