from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.apps import apps
from sync_app.models import ServerSyncLog
import json


@api_view(['GET'])
def sync_pull(request):
    """ارسال تمام داده‌ها از سرور اصلی به آفلاین"""
    try:
        print("📤 ارسال داده از سرور اصلی به آفلاین...")

        all_data = {
            'models': [],
            'changes': [],
            'summary': {'total_records': 0, 'total_models': 0}
        }

        # جمع‌آوری داده از تمام مدل‌ها
        for app_config in apps.get_app_configs():
            if any(app_config.name.startswith(excluded) for excluded in [
                'django.contrib.admin', 'django.contrib.auth',
                'django.contrib.contenttypes', 'django.contrib.sessions',
                'sync_app', 'sync_api'
            ]):
                continue

            for model in app_config.get_models():
                model_name = model.__name__
                if model_name in ['DataSyncLog', 'SyncSession', 'OfflineSetting', 'ServerSyncLog', 'SyncToken']:
                    continue

                try:
                    # سریالایز کردن تمام رکوردهای این مدل
                    model_data = []
                    for obj in model.objects.all()[:1000]:  # محدودیت برای جلوگیری از overload
                        serialized_data = {}
                        for field in obj._meta.get_fields():
                            if not field.is_relation or field.one_to_one:
                                try:
                                    value = getattr(obj, field.name)
                                    if hasattr(value, 'isoformat'):
                                        serialized_data[field.name] = value.isoformat()
                                    elif isinstance(value, (int, float, bool)):
                                        serialized_data[field.name] = value
                                    else:
                                        serialized_data[field.name] = str(value)
                                except:
                                    serialized_data[field.name] = None

                        model_data.append({
                            'id': obj.id,
                            'data': serialized_data
                        })

                    if model_data:
                        all_data['models'].append({
                            'app': app_config.name,
                            'model': model_name,
                            'record_count': len(model_data)
                        })

                        for item in model_data:
                            all_data['changes'].append({
                                'app_name': app_config.name,
                                'model_type': model_name,
                                'record_id': item['id'],
                                'action': 'sync',
                                'data': item['data']
                            })

                except Exception as e:
                    print(f"⚠️ خطا در سریالایز {model_name}: {e}")
                    continue

        all_data['summary']['total_records'] = len(all_data['changes'])
        all_data['summary']['total_models'] = len(all_data['models'])

        print(f"✅ ارسال {len(all_data['changes'])} رکورد از {len(all_data['models'])} مدل")

        return Response({
            'status': 'success',
            'message': f'داده از سرور اصلی ارسال شد',
            'payload': all_data
        })

    except Exception as e:
        print(f"❌ خطا در ارسال داده: {e}")
        return Response({'status': 'error', 'message': str(e)})


@api_view(['POST'])
def sync_receive(request):
    """دریافت تغییرات از سیستم‌های آفلاین"""
    try:
        data = request.data
        print(f"📩 دریافت تغییرات از آفلاین: {data.get('model_type')} - ID: {data.get('record_id')}")

        # ذخیره در لاگ سرور
        ServerSyncLog.objects.create(
            model_type=data.get('model_type'),
            record_id=data.get('record_id'),
            action=data.get('action'),
            data=data.get('data'),
            source_ip=request.META.get('REMOTE_ADDR', ''),
            sync_direction='local_to_server'
        )

        # اعمال تغییرات روی دیتابیس اصلی
        app_name = data.get('app_name', '')
        model_type = data.get('model_type')
        action = data.get('action')
        record_data = data.get('data', {})

        if app_name and model_type:
            try:
                model_class = apps.get_model(app_name, model_type)

                if action == 'create':
                    # برای ایجاد جدید، ID را حذف کن تا اتو اینکرمنت کار کند
                    create_data = record_data.copy()
                    if 'id' in create_data:
                        del create_data['id']
                    model_class.objects.create(**create_data)
                    print(f"✅ ایجاد شد: {model_type}")

                elif action == 'update':
                    # برای آپدیت، از ID استفاده کن
                    record_id = data.get('record_id')
                    if record_id:
                        model_class.objects.update_or_create(
                            id=record_id,
                            defaults=record_data
                        )
                        print(f"✅ آپدیت شد: {model_type} - ID: {record_id}")

            except Exception as e:
                print(f"⚠️ خطا در اعمال تغییرات: {e}")

        return Response({'status': 'success', 'message': 'تغییرات اعمال شد'})

    except Exception as e:
        print(f"❌ خطا در دریافت تغییرات: {e}")
        return Response({'status': 'error', 'message': str(e)})