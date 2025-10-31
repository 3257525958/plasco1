from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from sync_app.models import ServerSyncLog
from django.apps import apps


@api_view(['GET'])
def sync_pull(request):
    """ارسال داده‌ها به سیستم‌های آفلاین"""
    try:
        # کشف خودکار تمام مدل‌ها
        changes = []

        for app_config in apps.get_app_configs():
            if any(app_config.name.startswith(excluded) for excluded in [
                'django.contrib.admin', 'django.contrib.auth',
                'django.contrib.contenttypes', 'django.contrib.sessions'
            ]):
                continue

            for model in app_config.get_models():
                if model.__name__ in ['DataSyncLog', 'SyncSession', 'OfflineSetting', 'ServerSyncLog', 'SyncToken']:
                    continue

                # سریالایز کردن داده‌ها
                for obj in model.objects.all()[:100]:  # محدودیت برای تست
                    data = {}
                    for field in obj._meta.get_fields():
                        if not field.is_relation or field.one_to_one:
                            try:
                                value = getattr(obj, field.name)
                                if hasattr(value, 'isoformat'):
                                    data[field.name] = value.isoformat()
                                else:
                                    data[field.name] = str(value)
                            except:
                                data[field.name] = None

                    changes.append({
                        'app_name': app_config.name,
                        'model_type': model.__name__,
                        'record_id': obj.id,
                        'action': 'sync',
                        'data': data
                    })

        return Response({
            'status': 'success',
            'changes': changes,
            'total_changes': len(changes)
        })

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)})


@api_view(['POST'])
def sync_receive(request):
    """دریافت تغییرات از سیستم‌های آفلاین"""
    try:
        data = request.data
        print(f"📩 دریافت از آفلاین: {data.get('model_type')}")

        # ذخیره در لاگ سرور
        ServerSyncLog.objects.create(
            model_type=data.get('model_type'),
            record_id=data.get('record_id'),
            action=data.get('action'),
            data=data.get('data'),
            source_ip=request.META.get('REMOTE_ADDR'),
            sync_direction='local_to_server'
        )

        return Response({'status': 'success', 'message': 'دریافت شد'})

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)})