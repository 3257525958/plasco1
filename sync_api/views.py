from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.utils import timezone
# در sync_api/views.py سرور اصلی - ابتدای فایل
from django.db import models  # ← این خط را اضافه کن
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.utils import timezone
import decimal


@api_view(['GET'])
def sync_pull(request):
    """ارسال داده از سرور اصلی به آفلاین - با پشتیبانی سینک افزایشی مبتنی بر ID"""
    try:
        # دریافت پارامتر سینک افزایشی (آخرین ID سینک شده)
        last_sync_id_str = request.GET.get('last_sync_id')
        last_sync_id = int(last_sync_id_str) if last_sync_id_str and last_sync_id_str.isdigit() else 0

        print(f"📤 ارسال داده از سرور - آخرین ID سینک شده: {last_sync_id}")

        changes = []
        sync_mode = 'incremental' if last_sync_id > 0 else 'full'
        new_records_count = 0

        # لیست مدل‌های هدف
        target_models = [
            # account_app - مدل‌های اصلی
            'account_app.Product',
            'account_app.Customer',
            'account_app.Expense',
            'account_app.ExpenseImage',
            'account_app.FinancialDocument',
            'account_app.FinancialDocumentItem',
            'account_app.InventoryCount',
            'account_app.PaymentMethod',
            'account_app.ProductPricing',
            'account_app.StockTransaction',

            # cantact_app - مدل‌های ارتباطی
            # این مدل‌های cantact_app باید اضافه شوند:
            'cantact_app.Branch',
            'cantact_app.BranchAdmin',
            'cantact_app.accuntmodel',
            'cantact_app.dataacont',
            'cantact_app.phonnambermodel',
            'cantact_app.savecodphon',        ]

        for model_path in target_models:
            try:
                app_name, model_name = model_path.split('.')
                model_class = apps.get_model(app_name, model_name)

                # اعمال فیلتر سینک افزایشی بر اساس ID
                if sync_mode == 'incremental':
                    # فقط رکوردهای با ID بزرگتر از آخرین ID سینک شده
                    queryset = model_class.objects.filter(id__gt=last_sync_id)
                    new_records_count += queryset.count()
                    print(f"📈 {model_path}: {queryset.count()} رکورد جدید (ID > {last_sync_id})")
                else:
                    # سینک کامل - همه رکوردها
                    queryset = model_class.objects.all()
                    print(f"📦 {model_path}: {model_class.objects.count()} رکورد (سینک کامل)")

                # پیدا کردن حداکثر ID برای این مدل
                max_id = model_class.objects.aggregate(models.Max('id'))['id__max'] or 0

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

                # اضافه کردن اطلاعات حداکثر ID برای هر مدل
                changes.append({
                    'app_name': app_name,
                    'model_type': 'SyncInfo',
                    'record_id': 0,
                    'action': 'metadata',
                    'data': {
                        'max_id': max_id,
                        'model_name': model_name,
                        'total_records': model_class.objects.count()
                    },
                    'server_timestamp': timezone.now().isoformat(),
                    'sync_mode': sync_mode
                })

            except Exception as e:
                print(f"⚠️ خطا در پردازش {model_path}: {e}")
                continue

        # محاسبه حداکثر ID کلی
        overall_max_id = 0
        for change in changes:
            if change.get('action') == 'metadata' and change['data'].get('max_id', 0) > overall_max_id:
                overall_max_id = change['data']['max_id']

        # خلاصه عملکرد
        if sync_mode == 'incremental':
            print(
                f"🎯 سینک افزایشی: {new_records_count} رکورد جدید از {len([c for c in changes if c['action'] == 'sync'])} رکورد")
        else:
            print(f"🎯 سینک کامل: {len([c for c in changes if c['action'] == 'sync'])} رکورد")

        return Response({
            'status': 'success',
            'message': f'ارسال {len([c for c in changes if c["action"] == "sync"])} رکورد از سرور ({sync_mode})',
            'changes': changes,
            'total_changes': len([c for c in changes if c['action'] == 'sync']),
            'sync_mode': sync_mode,
            'new_records_count': new_records_count,
            'max_synced_id': overall_max_id,
            'server_timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        print(f"❌ خطا در سینک پول: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['POST'])
def sync_receive(request):
    """دریافت تغییرات از سیستم‌های آفلاین"""
    try:
        data = request.data
        print(f"📩 دریافت تغییرات از آفلاین: {data.get('model_type')}")

        # اعمال تغییرات روی دیتابیس اصلی
        app_name = data.get('app_name', '')
        model_type = data.get('model_type')
        action = data.get('action')
        record_data = data.get('data', {})

        if app_name and model_type:
            try:
                model_class = apps.get_model(app_name, model_type)

                if action == 'create':
                    # برای ایجاد جدید
                    create_data = {k: v for k, v in record_data.items() if k != 'id'}
                    model_class.objects.create(**create_data)
                    print(f"✅ ایجاد شد: {model_type}")

                elif action == 'update':
                    # برای آپدیت
                    record_id = data.get('record_id')
                    if record_id:
                        model_class.objects.update_or_create(
                            id=record_id,
                            defaults=record_data
                        )
                        print(f"✅ آپدیت شد: {model_type} - ID: {record_id}")

            except Exception as e:
                print(f"⚠️ خطا در اعمال تغییرات: {e}")

        return Response({
            'status': 'success',
            'message': 'تغییرات اعمال شد'
        })

    except Exception as e:
        print(f"❌ خطا در دریافت تغییرات: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)