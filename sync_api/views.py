from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps


@api_view(['GET'])
def sync_pull(request):
    """ارسال داده از سرور اصلی به آفلاین"""
    try:
        print("📤 ارسال داده از سرور اصلی به آفلاین...")

        changes = []

        # فقط مدل‌های اصلی کسب و کار
        # لیست کامل تمام مدل‌های مهم
        target_models = [
            # account_app
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

            # cantact_app
            'cantact_app.Branch',
            'cantact_app.BranchAdmin',
            'cantact_app.accuntmodel',
            'cantact_app.dataacont',
            'cantact_app.phonnambermodel',
            'cantact_app.savecodphon',

            # dashbord_app
            'dashbord_app.BankAccount',
            'dashbord_app.ContactNumber',
            'dashbord_app.Froshande',
            'dashbord_app.Invoice',
            'dashbord_app.InvoiceItem',
            'dashbord_app.Product',

            # invoice_app
            'invoice_app.Invoicefrosh',
            'invoice_app.InvoiceItemfrosh',
            'invoice_app.CheckPayment',
            'invoice_app.CreditPayment',
            'invoice_app.POSDevice',
            'invoice_app.POSTransaction',

            # pos_payment
            'pos_payment.POSTransaction',
        ]


        for model_path in target_models:
            try:
                app_name, model_name = model_path.split('.')
                model_class = apps.get_model(app_name, model_name)

                for obj in model_class.objects.all():  # همه رکوردها                    data = {}
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
                        'data': data
                    })

            except Exception as e:
                print(f"⚠️ خطا در پردازش {model_path}: {e}")
                continue

        return Response({
            'status': 'success',
            'message': f'ارسال {len(changes)} رکورد از سرور',
            'changes': changes,
            'total_changes': len(changes)
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