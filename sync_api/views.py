from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.utils import timezone
import decimal
@api_view(['GET'])
def sync_pull(request):
    """ارسال داده از سرور اصلی به آفلاین - با پشتیبانی سینک افزایشی"""
    try:
        # دریافت پارامتر سینک افزایشی
        last_sync_str = request.GET.get('last_sync')
        last_sync = None
        if last_sync_str:
            try:
                last_sync = timezone.datetime.fromisoformat(last_sync_str.replace('Z', '+00:00'))
            except:
                pass

        print(f"📤 ارسال داده از سرور - سینک افزایشی: {last_sync}")

        changes = []
        sync_mode = 'incremental' if last_sync else 'full'

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

                # فیلتر بر اساس زمان برای سینک افزایشی
                queryset = model_class.objects.all()
                if last_sync and hasattr(model_class, 'updated_at'):
                    queryset = queryset.filter(updated_at__gt=last_sync)
                elif last_sync and hasattr(model_class, 'created_at'):
                    queryset = queryset.filter(created_at__gt=last_sync)

                for obj in queryset:
                    # سریالایز کردن داده‌ها (کد موجود)
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

                if sync_mode == 'incremental':
                    print(f"📈 {model_path}: {queryset.count()} رکورد جدید/تغییر کرده")
                else:
                    print(f"📦 {model_path}: {model_class.objects.count()} رکورد")

            except Exception as e:
                print(f"⚠️ خطا در پردازش {model_path}: {e}")
                continue

        return Response({
            'status': 'success',
            'message': f'ارسال {len(changes)} رکورد از سرور ({sync_mode})',
            'changes': changes,
            'total_changes': len(changes),
            'sync_mode': sync_mode,
            'server_timestamp': timezone.now().isoformat(),
            'next_sync_recommended': timezone.now().isoformat()
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