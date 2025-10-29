from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  # 🔥 این خط را اضافه کنید
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from account_app.models import Product
from .models import ServerSyncLog, SyncToken
import json


@api_view(['GET'])
@permission_classes([AllowAny])  # 🔥 این خط را جایگزین IsAuthenticated کنید
def sync_pull(request):
    """ارسال داده به کامپیوترهای آفلاین"""
    try:
        # 🔍 بررسی توکن دستی
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return Response({
                'status': 'error',
                'message': 'توکن ارسال نشده است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token_key = auth_header[6:]  # حذف 'Token '

        # بررسی توکن در دیتابیس
        try:
            token = SyncToken.objects.get(token=token_key, is_active=True)
            print(f"✅ توکن معتبر: {token.name}")
        except SyncToken.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'توکن نامعتبر است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # ادامه کد فعلی شما...
        changes = []

        # محصولات جدید
        products = Product.objects.filter(updated_at__gte=timezone.now() - timezone.timedelta(hours=24))
        for product in products:
            changes.append({
                'model_type': 'product',
                'record_id': product.id,
                'action': 'update',
                'data': {
                    'name': product.name,
                    'description': product.description
                },
                'server_timestamp': product.updated_at.isoformat()
            })

        return Response({
            'changes': changes,
            'count': len(changes)
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)