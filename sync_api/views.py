from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps


@api_view(['GET'])
def sync_pull(request):
    """ارسال داده‌ها به سیستم‌های آفلاین"""
    try:
        changes = []

        for app_config in apps.get_app_configs():
            # نادیده گرفتن اپ‌های سیستمی
            if any(app_config.name.startswith(excluded) for excluded in [
                'django.contrib.admin', 'django.contrib.auth',
                'django.contrib.contenttypes', 'django.contrib.sessions',
                'sync_app', 'sync_api'
            ]):
                continue

            for model in app_config.get_models():
                model_name = model.__name__
                # نادیده گرفتن مدل‌های سینک
                if model_name in ['DataSyncLog', 'SyncSession', 'OfflineSetting', 'ServerSyncLog', 'SyncToken']:
                    continue

                try:
                    # سریالایز کردن داده‌ها با محدودیت
                    for obj in model.objects.all()[:50]:  # محدودیت بیشتر
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
                            'model_type': model_name,
                            'record_id': obj.id,
                            'action': 'sync',
                            'data': data
                        })
                except Exception as e:
                    print(f"⚠️ خطا در سریالایز مدل {model_name}: {e}")
                    continue

        return Response({
            'status': 'success',
            'changes': changes,
            'total_changes': len(changes)
        })

    except Exception as e:
        print(f"❌ خطا در سینک پول: {e}")
        return Response({'status': 'error', 'message': str(e)})


@api_view(['POST'])
def sync_receive(request):
    """دریافت تغییرات از سیستم‌های آفلاین"""
    try:
        data = request.data
        print(f"📩 دریافت از آفلاین: {data.get('model_type')}")

        # فقط اگر مدل ServerSyncLog وجود دارد
        try:
            from sync_app.models import ServerSyncLog
            ServerSyncLog.objects.create(
                model_type=data.get('model_type'),
                record_id=data.get('record_id'),
                action=data.get('action'),
                data=data.get('data'),
                source_ip=request.META.get('REMOTE_ADDR', ''),
                sync_direction='local_to_server'
            )
        except Exception as e:
            print(f"⚠️ خطا در ذخیره لاگ سرور: {e}")

        return Response({'status': 'success', 'message': 'دریافت شد'})

    except Exception as e:
        print(f"❌ خطا در دریافت: {e}")
        return Response({'status': 'error', 'message': str(e)})