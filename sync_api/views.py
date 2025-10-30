from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import SyncToken


@api_view(['GET'])
@authentication_classes([])  # 🔥 غیرفعال کردن کامل authentication
@permission_classes([])  # 🔥 غیرفعال کردن کامل permission
def sync_pull(request):
    """سینک همه مدل‌های اصلی - بدون هیچ authentication"""
    try:
        print("🔄 درخواست sync_pull دریافت شد - نسخه بدون احراز هویت")

        # بررسی توکن به صورت دستی
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        print(f"📨 هدر احراز: {auth_header}")

        if not auth_header.startswith('Token '):
            return Response({
                'status': 'error',
                'message': 'توکن ارسال نشده است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token_key = auth_header[6:]
        print(f"🔑 توکن دریافت شده: {token_key}")

        # بررسی توکن در دیتابیس
        try:
            token = SyncToken.objects.get(token=token_key, is_active=True)
            print(f"✅ توکن معتبر: {token.name}")
        except SyncToken.DoesNotExist:
            print("❌ توکن نامعتبر")
            return Response({
                'status': 'error',
                'message': 'توکن نامعتبر است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        changes = []

        # 🔥 مدل‌های اصلی از account_app
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
                        'name': product.name,
                        'description': product.description or '',
                        'created_at': product.created_at.isoformat() if product.created_at else timezone.now().isoformat(),
                        'updated_at': product.updated_at.isoformat() if product.updated_at else timezone.now().isoformat()
                    }
                })
            print(f"✅ محصولات: {len(products)} رکورد")
        except Exception as e:
            print(f"⚠️ خطا در محصولات: {e}")

        # 🔥 مدل‌های از dashbord_app
        try:
            from dashbord_app.models import Froshande, Product as DashProduct
            # فروشندگان
            froshandes = Froshande.objects.all()[:50]
            for froshande in froshandes:
                changes.append({
                    'app_name': 'dashbord_app',
                    'model_type': 'Froshande',
                    'record_id': froshande.id,
                    'action': 'create_or_update',
                    'data': {
                        'name': froshande.name or '',
                        'family': froshande.family or '',
                        'store_name': froshande.store_name or '',
                        'address': froshande.address or ''
                    }
                })

            # محصولات dashbord
            dash_products = DashProduct.objects.all()[:50]
            for product in dash_products:
                changes.append({
                    'app_name': 'dashbord_app',
                    'model_type': 'Product',
                    'record_id': product.id,
                    'action': 'create_or_update',
                    'data': {
                        'name': product.name or '',
                        'barcode': product.barcode or '',
                        'unit_price': str(product.unit_price) if product.unit_price else '0'
                    }
                })
            print(f"✅ فروشندگان: {len(froshandes)}، محصولات: {len(dash_products)}")
        except Exception as e:
            print(f"⚠️ خطا در dashbord_app: {e}")

        # 🔥 مدل‌های از invoice_app
        try:
            from invoice_app.models import Invoicefrosh
            invoices = Invoicefrosh.objects.all()[:30]
            for invoice in invoices:
                changes.append({
                    'app_name': 'invoice_app',
                    'model_type': 'Invoicefrosh',
                    'record_id': invoice.id,
                    'action': 'create_or_update',
                    'data': {
                        'branch': invoice.branch.name if invoice.branch else '',
                        'created_at': invoice.created_at.isoformat() if invoice.created_at else timezone.now().isoformat()
                    }
                })
            print(f"✅ فاکتورها: {len(invoices)}")
        except Exception as e:
            print(f"⚠️ خطا در فاکتورها: {e}")

        print(f"📤 ارسال {len(changes)} رکورد از {len([c for c in changes if c['app_name'] == 'account_app'])} مدل")

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

        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)