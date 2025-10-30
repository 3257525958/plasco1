from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import SyncToken
from account_app.models import Product  # 🔥 مدل واقعی
from cantact_app.models import Contact  # 🔥 مدل واقعی
from invoice_app.models import Invoice  # 🔥 مدل واقعی


@api_view(['GET'])
def sync_pull(request):
    """ارسال داده‌های واقعی به کامپیوترهای آفلاین"""
    try:
        print("🔄 درخواست sync_pull دریافت شد")

        # بررسی توکن
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Token '):
            return Response({
                'status': 'error',
                'message': 'توکن ارسال نشده است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token_key = auth_header[6:]

        # بررسی توکن در دیتابیس
        try:
            token = SyncToken.objects.get(token=token_key, is_active=True)
            print(f"✅ توکن معتبر: {token.name}")
        except SyncToken.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'توکن نامعتبر است'
            }, status=status.HTTP_401_UNAUTHORIZED)

        changes = []

        # 🔥 محصولات واقعی
        products = Product.objects.all()[:50]  # 50 محصول اول
        for product in products:
            changes.append({
                'model_type': 'product',
                'record_id': product.id,
                'action': 'create',
                'data': {
                    'name': product.name,
                    'description': product.description,
                    'price': str(product.price) if hasattr(product, 'price') else '0',
                    # سایر فیلدهای محصول
                },
                'server_timestamp': product.updated_at.isoformat() if hasattr(product,
                                                                              'updated_at') else timezone.now().isoformat()
            })

        # 🔥 مخاطبین واقعی
        try:
            contacts = Contact.objects.all()[:50]  # 50 مخاطب اول
            for contact in contacts:
                changes.append({
                    'model_type': 'contact',
                    'record_id': contact.id,
                    'action': 'create',
                    'data': {
                        'name': contact.name,
                        'phone': contact.phone,
                        'email': getattr(contact, 'email', ''),
                        # سایر فیلدهای مخاطب
                    },
                    'server_timestamp': contact.updated_at.isoformat() if hasattr(contact,
                                                                                  'updated_at') else timezone.now().isoformat()
                })
        except Exception as e:
            print(f"⚠️ خطا در دریافت مخاطبین: {e}")

        # 🔥 فاکتورهای واقعی
        try:
            invoices = Invoice.objects.all()[:30]  # 30 فاکتور اول
            for invoice in invoices:
                changes.append({
                    'model_type': 'invoice',
                    'record_id': invoice.id,
                    'action': 'create',
                    'data': {
                        'invoice_number': invoice.invoice_number,
                        'customer_name': getattr(invoice, 'customer_name', ''),
                        'total_amount': str(getattr(invoice, 'total_amount', 0)),
                        'date': invoice.date.isoformat() if hasattr(invoice, 'date') else timezone.now().isoformat(),
                        # سایر فیلدهای فاکتور
                    },
                    'server_timestamp': invoice.updated_at.isoformat() if hasattr(invoice,
                                                                                  'updated_at') else timezone.now().isoformat()
                })
        except Exception as e:
            print(f"⚠️ خطا در دریافت فاکتورها: {e}")

        print(f"📤 ارسال {len(changes)} رکورد واقعی")

        return Response({
            'status': 'success',
            'message': 'همگام‌سازی موفق',
            'changes': changes,
            'count': len(changes)
        })

    except Exception as e:
        print(f"❌ خطا در sync_pull: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)