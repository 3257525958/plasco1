
from django.db import models  # ← این خط را اضافه کن
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.utils import timezone
import decimal


@api_view(['GET'])
def sync_pull(request):
    """ارسال داده از سرور اصلی به آفلاین - نسخه هوشمند مبتنی بر ID"""
    try:
        # دریافت پارامتر سینک افزایشی مبتنی بر ID
        last_sync_id_str = request.GET.get('last_sync_id')
        last_sync_id = int(last_sync_id_str) if last_sync_id_str and last_sync_id_str.isdigit() else 0

        print(f"📤 ارسال داده از سرور - آخرین ID سینک شده: {last_sync_id}")

        changes = []
        sync_mode = 'incremental' if last_sync_id > 0 else 'full'
        new_records_count = 0
        overall_max_id = 0

        # لیست مدل‌های هدف
        target_models = [
            'cantact_app.Branch',
            'cantact_app.BranchAdmin',
            'cantact_app.accuntmodel',
            'cantact_app.dataacont',
            'cantact_app.phonnambermodel',
            'cantact_app.savecodphon',
        ]

        for model_path in target_models:
            try:
                app_name, model_name = model_path.split('.')
                model_class = apps.get_model(app_name, model_name)

                # 🔥 منطق جدید: فقط رکوردهای با ID بزرگتر
                if sync_mode == 'incremental':
                    queryset = model_class.objects.filter(id__gt=last_sync_id)
                    new_records_count += queryset.count()
                    print(f"📈 {model_path}: {queryset.count()} رکورد جدید (ID > {last_sync_id})")
                else:
                    queryset = model_class.objects.all()
                    print(f"📦 {model_path}: {model_class.objects.count()} رکورد (سینک کامل)")

                # پیدا کردن حداکثر ID برای این مدل
                max_id = model_class.objects.aggregate(models.Max('id'))['id__max'] or 0
                if max_id > overall_max_id:
                    overall_max_id = max_id

                for obj in queryset:
                    data = {}
                    for field in obj._meta.get_fields():
                        if not field.is_relation or field.one_to_one:
                            try:
                                value = getattr(obj, field.name)
                                if hasattr(value, 'isoformat'):
                                    data[field.name] = value.isoformat()
                                elif isinstance(value, (int, float, bool)):
                                    data[field.name] = value
                                else:
                                    data[field.name] = str(value)
                            except:
                                data[field.name] = None

                    changes.append({
                        'app_name': app_name,
                        'model_type': model_name,
                        'record_id': obj.id,
                        'action': 'sync',
                        'data': data,
                        'server_timestamp': timezone.now().isoformat(),
                        'sync_mode': sync_mode
                    })

            except Exception as e:
                print(f"⚠️ خطا در پردازش {model_path}: {e}")
                continue

        print(f"🎯 ارسال {len(changes)} رکورد ({sync_mode}) - حداکثر ID: {overall_max_id}")

        return Response({
            'status': 'success',
            'message': f'ارسال {len(changes)} رکورد از سرور ({sync_mode})',
            'changes': changes,
            'total_changes': len(changes),
            'sync_mode': sync_mode,
            'new_records_count': new_records_count,
            'max_synced_id': overall_max_id,  # 🔥 این خط مهم است!
            'server_timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        print(f"❌ خطا در سینک پول: {e}")
        return Response({'status': 'error', 'message': str(e)})
@api_view(['POST'])
def sync_receive(request):
    """دریافت تغییرات از سیستم‌های آفلاین - نسخه کاملاً اصلاح شده"""
    try:
        data = request.data
        print(f"📩 دریافت تغییرات از آفلاین: {data.get('model_type')}")

        app_name = data.get('app_name', '')
        model_type = data.get('model_type')
        action = data.get('action')
        record_id = data.get('record_id')
        record_data = data.get('data', {})

        print(f"🔍 پارامترها: app={app_name}, model={model_type}, action={action}, id={record_id}")
        print(f"📦 داده‌ها: {record_data}")

        if app_name and model_type:
            try:
                # دریافت مدل
                model_class = apps.get_model(app_name, model_type)
                print(f"✅ مدل پیدا شد: {model_class}")

                if action == 'create':
                    # برای ایجاد جدید - حذف id از داده‌ها
                    create_data = {k: v for k, v in record_data.items() if k != 'id'}
                    print(f"📝 ایجاد با داده: {create_data}")

                    # ایجاد آبجکت جدید
                    new_obj = model_class.objects.create(**create_data)
                    print(f"✅ ایجاد شد: {model_type} - ID جدید: {new_obj.id}")

                    return Response({
                        'status': 'success',
                        'message': f'ایجاد شد: {model_type} - ID: {new_obj.id}',
                        'new_id': new_obj.id
                    })

                elif action == 'update':
                    print(f"📝 آپدیت با داده: {record_data}")

                    # آپدیت یا ایجاد
                    obj, created = model_class.objects.update_or_create(
                        id=record_id,
                        defaults=record_data
                    )

                    action_text = "ایجاد" if created else "آپدیت"
                    print(f"✅ {action_text} شد: {model_type} - ID: {obj.id}")

                    return Response({
                        'status': 'success',
                        'message': f'{action_text} شد: {model_type} - ID: {obj.id}',
                        'action': action_text
                    })

                else:
                    return Response({
                        'status': 'error',
                        'message': f'عملیت نامعتبر: {action}'
                    }, status=400)

            except Exception as e:
                print(f"❌ خطا در پردازش مدل: {e}")
                import traceback
                print(f"📋 جزئیات خطا: {traceback.format_exc()}")

                return Response({
                    'status': 'error',
                    'message': f'خطا در پردازش مدل: {str(e)}'
                }, status=400)

        else:
            return Response({
                'status': 'error',
                'message': 'پارامترهای ناقص: app_name و model_type الزامی هستند'
            }, status=400)

    except Exception as e:
        print(f"❌ خطا در دریافت تغییرات: {e}")
        import traceback
        print(f"📋 جزئیات خطا: {traceback.format_exc()}")

        return Response({
            'status': 'error',
            'message': f'خطای سرور: {str(e)}'
        }, status=500)