from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth.models import User
from account_app.models import Product
from .models import ServerSyncLog, SyncToken
import json


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_push(request):
    """دریافت داده از کامپیوترهای آفلاین"""
    try:
        data = request.data

        # ثبت در لاگ سرور
        sync_log = ServerSyncLog.objects.create(
            model_type=data['model_type'],
            record_id=data['record_id'],
            action=data['action'],
            data=data['data'],
            source_ip=request.META.get('REMOTE_ADDR', 'unknown'),
            sync_direction='local_to_server'
        )

        # پردازش ساده داده
        if data['model_type'] == 'product':
            if data['action'] == 'create':
                Product.objects.create(
                    name=data['data']['name'],
                    description=data['data'].get('description', '')
                )

        sync_log.processed = True
        sync_log.processed_at = timezone.now()
        sync_log.save()

        return Response({
            'status': 'success',
            'message': 'داده دریافت شد',
            'log_id': sync_log.id
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_pull(request):
    """ارسال داده به کامپیوترهای آفلاین"""
    try:
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