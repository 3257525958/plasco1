from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import SyncToken


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def sync_pull(request):
    """سینک همه مدل‌ها با نام‌های دقیق"""
    try:
        print("🔄 درخواست sync_pull برای همه مدل‌ها")

        # بررسی توکن
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Token '):
            return Response({
                'status': 'error',
                'message': 'توکن ارسال نشده است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token_key = auth_header[6:]

        try:
            token = SyncToken.objects.get(token=token_key, is_active=True)
            print(f"✅ توکن معتبر: {token.name}")
        except SyncToken.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'توکن نامعتبر است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        changes = []

        # 🔥 ۱. کاربران سیستم
        try:
            from django.contrib.auth.models import User
            users = User.objects.all()[:100]
            for user in users:
                user_data = {
                    'username': user.username,
                    'email': user.email or '',
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else '',
                    'password': user.password  # 🔥 مهم: هش پسورد
                }
                changes.append({
                    'app_name': 'auth',
                    'model_type': 'User',
                    'record_id': user.id,
                    'action': 'create_or_update',
                    'data': user_data
                })
            print(f"✅ کاربران سیستم: {len(users)}")
        except Exception as e:
            print(f"⚠️ خطا در کاربران: {e}")

        # 🔥 ۲. account_app
        try:
            from account_app.models import Product
            products = Product.objects.all()[:100]
            for product in products:
                changes.append({
                    'app_name': 'account_app',
                    'model_type': 'Product',
                    'record_id': product.id,
                    'action': 'create_or_update',
                    'data': {
                        'name': product.name or '',
                        'description': product.description or '',
                        'created_at': product.created_at.isoformat() if product.created_at else '',
                        'updated_at': product.updated_at.isoformat() if product.updated_at else ''
                    }
                })
            print(f"✅ محصولات: {len(products)}")
        except Exception as e:
            print(f"⚠️ خطا در محصولات: {e}")

        # 🔥 ۳. dashbord_app - با نام‌های دقیق
        try:
            from dashbord_app.models import Froshande
            froshandes = Froshande.objects.all()[:100]
            for frosh in froshandes:
                changes.append({
                    'app_name': 'dashbord_app',
                    'model_type': 'Froshande',
                    'record_id': frosh.id,
                    'action': 'create_or_update',
                    'data': {
                        'name': frosh.name or '',
                        'family': frosh.family or '',
                        'store_name': frosh.store_name or '',
                        'address': frosh.address or ''
                    }
                })
            print(f"✅ فروشندگان: {len(froshandes)}")
        except Exception as e:
            print(f"⚠️ خطا در فروشندگان: {e}")

        # 🔥 ۴. cantact_app - با نام‌های دقیق
        try:
            from cantact_app.models import accuntmodel
            accounts = accuntmodel.objects.all()[:100]
            for acc in accounts:
                changes.append({
                    'app_name': 'cantact_app',
                    'model_type': 'accuntmodel',  # 🔥 با حروف کوچک
                    'record_id': acc.id,
                    'action': 'create_or_update',
                    'data': {
                        'firstname': acc.firstname or '',
                        'lastname': acc.lastname or '',
                        'melicode': acc.melicode or '',
                        'phonnumber': acc.phonnumber or ''
                    }
                })
            print(f"✅ حساب‌های کاربری: {len(accounts)}")
        except Exception as e:
            print(f"⚠️ خطا در حساب‌های کاربری: {e}")

        # 🔥 ۵. invoice_app - با نام‌های دقیق
        try:
            from invoice_app.models import Invoicefrosh
            invoices = Invoicefrosh.objects.all()[:50]
            for inv in invoices:
                # برای فیلدهای ForeignKey فقط ID را می‌فرستیم
                invoice_data = {
                    'created_at': inv.created_at.isoformat() if inv.created_at else '',
                    'payment_date': inv.payment_date.isoformat() if inv.payment_date else ''
                }
                # اضافه کردن فیلدهای معمولی
                if hasattr(inv, 'branch_id') and inv.branch_id:
                    invoice_data['branch_id'] = inv.branch_id

                changes.append({
                    'app_name': 'invoice_app',
                    'model_type': 'Invoicefrosh',
                    'record_id': inv.id,
                    'action': 'create_or_update',
                    'data': invoice_data
                })
            print(f"✅ فاکتورها: {len(invoices)}")
        except Exception as e:
            print(f"⚠️ خطا در فاکتورها: {e}")

        print(f"📤 ارسال {len(changes)} رکورد از {len(set([c['app_name'] for c in changes]))} اپ")

        return Response({
            'status': 'success',
            'message': f'همگام‌سازی {len(changes)} رکورد موفق',
            'changes': changes,
            'total_records': len(changes)
        })

    except Exception as e:
        print(f"❌ خطا در sync_pull: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'status': 'error', 'message': str(e)})