from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q, Sum
import json
from cantact_app.models import Branch
from dashbord_app.models import Invoice, InvoiceItem, Product, Froshande
from .models import *
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q, Sum
import json
from cantact_app.models import Branch
from dashbord_app.models import Invoice, InvoiceItem, Product, Froshande
from .models import *

def inventory_management(request):
    branches = Branch.objects.all()
    products = Product.objects.all()
    return render(request, 'inventory_management.html', {
        'branches': branches,
        'products': products
    })
#


# ----------------------------------------------------------------------
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
import json
import logging
from .models import InventoryCount, Branch, Product
from .utils import convert_persian_arabic_to_english

logger = logging.getLogger(__name__)


def get_branches(request):
    try:
        branches = Branch.objects.all().values('id', 'name', 'address')
        return JsonResponse({
            'success': True,
            'branches': list(branches)
        })
    except Exception as e:
        logger.error(f"Error in get_branches: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در دریافت اطلاعات شعب'
        })


def search_products(request):
    try:
        query = request.GET.get('q', '')
        branch_id = request.GET.get('branch_id', '')

        # تبدیل اعداد فارسی/عربی به انگلیسی
        query_english = convert_persian_arabic_to_english(query)

        if len(query_english) < 2:
            return JsonResponse({'results': []})

        # جستجو در محصولات از مدل InventoryCount بدون در نظر گرفتن شعبه
        products_query = InventoryCount.objects.filter(
            Q(product_name__icontains=query_english) |
            Q(product_name__icontains=query)
        )

        # دریافت نام محصولات متمایز (بدون در نظر گرفتن شعبه)
        products = products_query.values_list('product_name', flat=True).distinct()[:10]

        results = []
        for product_name in products:
            results.append({
                'id': product_name,  # استفاده از نام محصول به عنوان ID
                'text': product_name,
                'type': 'product'
            })

        return JsonResponse({'results': results})

    except Exception as e:
        logger.error(f"Error in product search: {str(e)}")
        return JsonResponse({'results': []})
def check_product(request):
    try:
        product_name = request.GET.get('product_name', '')
        branch_id = request.GET.get('branch_id', '')

        if not product_name or not branch_id:
            return JsonResponse({
                'exists': False,
                'last_counts': []
            })

        # بررسی وجود محصول در انبار
        exists = InventoryCount.objects.filter(
            product_name=product_name,
            branch_id=branch_id
        ).exists()

        last_counts = []
        if exists:
            # دریافت تاریخچه شمارش‌های قبلی
            last_counts = InventoryCount.objects.filter(
                product_name=product_name,
                branch_id=branch_id
            ).order_by('-created_at')[:5].values('count_date', 'counter__username', 'quantity')

        return JsonResponse({
            'exists': exists,
            'last_counts': list(last_counts)
        })

    except Exception as e:
        logger.error(f"Error in check_product: {str(e)}")
        return JsonResponse({
            'exists': False,
            'last_counts': []
        })


# @method_decorator(csrf_exempt, name='dispatch')
# class UpdateInventoryCount(View):
#     def post(self, request):
#         try:
#             # بررسی اینکه کاربر لاگین کرده است یا نه
#             if not request.user.is_authenticated:
#                 return JsonResponse({
#                     'success': False,
#                     'error': 'لطفاً ابتدا وارد سیستم شوید'
#                 })
#
#             data = json.loads(request.body)
#             items = data.get('items', [])
#             user = request.user
#
#             for item in items:
#                 # ایجاد یا به روزرسانی رکورد شمارش
#                 inventory_count, created = InventoryCount.objects.update_or_create(
#                     product_name=item['productName'],
#                     branch_id=item['branchId'],
#                     defaults={
#                         'is_new': item['productType'] == 'new',
#                         'quantity': item['quantity'],
#                         'counter': user
#                     }
#                 )
#
#             return JsonResponse({
#                 'success': True,
#                 'message': 'انبار با موفقیت به روزرسانی شد'
#             })
#
#         except Exception as e:
#             logger.error(f"Error in update_inventory_count: {str(e)}")
#             return JsonResponse({
#                 'success': False,
#                 'error': str(e)
#             })


@method_decorator(csrf_exempt, name='dispatch')
class UpdateInventoryCount(View):
    def post(self, request):
        try:
            # بررسی اینکه کاربر لاگین کرده است یا نه
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'لطفاً ابتدا وارد سیستم شوید'
                })

            data = json.loads(request.body)
            items = data.get('items', [])
            user = request.user

            # لاگ کردن اطلاعات دریافتی برای دیباگ
            logger.info(f"Received items: {items}")

            for item in items:
                # لاگ کردن هر آیتم برای دیباگ
                logger.info(f"Processing item: {item}")

                # ایجاد یا به روزرسانی رکورد شمارش
                inventory_count, created = InventoryCount.objects.update_or_create(
                    product_name=item['productName'],
                    branch_id=item['branchId'],
                    defaults={
                        'is_new': item.get('productType', 'new') == 'new',  # استفاده از get با مقدار پیشفرض
                        'quantity': item['quantity'],
                        'counter': user
                    }
                )

            return JsonResponse({
                'success': True,
                'message': 'انبار با موفقیت به روزرسانی شد'
            })

        except Exception as e:
            logger.error(f"Error in update_inventory_count: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


# ------------------------------------------------------------------------------------------
# views.py
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from .models import InventoryCount, Branch
from dashbord_app.models import Invoice, InvoiceItem, Froshande
from .utils import convert_persian_arabic_to_english
from django.shortcuts import render


@require_GET
def search_invoices(request):
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'results': []})

    # جستجو در شماره سریال و نام فروشنده
    invoices = Invoice.objects.filter(
        Q(serial_number__icontains=query) |
        Q(seller__name__icontains=query)  # اگر مدل Froshande فیلد name دارد
    )[:10]  # محدود کردن نتایج به 10 مورد

    results = []
    for invoice in invoices:
        results.append({
            'id': invoice.id,
            'serial_number': invoice.serial_number,
            'seller_name': str(invoice.seller),  # یا invoice.seller.name
            'date': invoice.jalali_date,
            'text': f"{invoice.serial_number} - {invoice.seller}"
        })

    return JsonResponse({'results': results})
# Get invoice details and items
def get_invoice_details(request):
    try:
        invoice_id = request.GET.get('invoice_id', '')

        if not invoice_id:
            return JsonResponse({'success': False, 'error': 'Invoice ID is required'})

        invoice = Invoice.objects.get(id=invoice_id)
        items = invoice.items.all()

        invoice_data = {
            'id': invoice.id,
            'serial_number': invoice.serial_number,
            'seller_name': f"{invoice.seller.name} {invoice.seller.family}",
            'date': invoice.jalali_date
        }

        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'product_name': item.product_name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'selling_price': str(item.selling_price)
            })

        return JsonResponse({
            'success': True,
            'invoice': invoice_data,
            'items': items_data
        })

    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'فاکتور یافت نشد'})
    except Exception as e:
        logger.error(f"Error getting invoice details: {str(e)}")
        return JsonResponse({'success': False, 'error': 'خطا در دریافت اطلاعات فاکتور'})
import sys
import arabic_reshaper
from bidi.algorithm import get_display
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

# تنظیم encoding پیشفرض به UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# تنظیمات reshaper برای فارسی
arabic_reshaper.configuration_for_arabic_letters = {
    'delete_harakat': False,
    'support_ligatures': True,
    'language': 'Farsi',
}

import sys
import arabic_reshaper
from bidi.algorithm import get_display
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
import json
import logging
from decimal import Decimal
from datetime import datetime

# مدل‌های مورد نیاز را import کنید
from .models import InventoryCount, Branch
from dashbord_app.models import Invoice, InvoiceItem
from account_app.models import FinancialDocument, FinancialDocumentItem  # فرض می‌کنیم این مدل‌ها وجود دارند



def persian_print(text):
    """تابع کمکی برای نمایش متن فارسی در کنسول"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    print(bidi_text)

# تنظیمات reshaper برای فارسی
arabic_reshaper.configuration_for_arabic_letters = {
    'delete_harakat': False,
    'support_ligatures': True,
    'language': 'Farsi',
}
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
import json
import logging
from decimal import Decimal
from datetime import datetime
@method_decorator(csrf_exempt, name='dispatch')
class StoreInvoiceItems(View):
    @transaction.atomic
    def post(self, request):
        try:
            # بررسی توکن یکبار مصرف
            data = json.loads(request.body)
            request_id = data.get('request_id')

            if request_id:
                cache_key = f"invoice_request_{request_id}"
                if cache.get(cache_key):
                    return JsonResponse({'success': False, 'error': 'این درخواست قبلاً پردازش شده است'})
                cache.set(cache_key, True, timeout=300)

            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'error': 'لطفاً ابتدا وارد سیستم شوید'})

            items = data.get('items', [])
            invoice_id = data.get('invoice_id')

            if not invoice_id:
                return JsonResponse({'success': False, 'error': 'شناسه فاکتور الزامی است'})

            # دریافت اطلاعات فاکتور
            try:
                invoice = Invoice.objects.get(id=invoice_id)
                invoice_items = InvoiceItem.objects.filter(invoice=invoice)
            except Invoice.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'فاکتور یافت نشد'})

            # ایجاد دیکشنری برای جمع‌بندی مقادیر ذخیره‌شده برای هر محصول
            stored_quantities = {}
            for item in items:
                product_name = item.get('product_name')
                quantity = int(item.get('quantity', 0))
                if product_name in stored_quantities:
                    stored_quantities[product_name] += quantity
                else:
                    stored_quantities[product_name] = quantity

            # به روزرسانی مقدار remaining_quantity برای هر آیتم فاکتور
            for invoice_item in invoice_items:
                product_name = invoice_item.product_name
                if product_name in stored_quantities:
                    # کسر مقدار ثبت شده از مقدار باقیمانده
                    new_remaining = invoice_item.remaining_quantity - stored_quantities[product_name]
                    invoice_item.remaining_quantity = max(0, new_remaining)
                    invoice_item.save()

            # ایجاد یک دیکشنری برای ذخیره مقادیر هر محصول در هر شعبه
            product_branch_totals = {}
            print_data = {
                'invoice_number': invoice.serial_number if invoice else 'نامشخص',
                'items': {}
            }

            for item in items:
                branch_id = item.get('branch_id')
                quantity = int(item.get('quantity'))
                product_name = item.get('product_name')

                if not branch_id or not product_name:
                    continue

                try:
                    branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'شعبه با شناسه {branch_id} یافت نشد'})

                # ایجاد کلید منحصر به فرد برای هر محصول در هر شعبه
                product_branch_key = f"{product_name}_{branch_id}"

                if product_branch_key not in product_branch_totals:
                    product_branch_totals[product_branch_key] = {
                        'product_name': product_name,
                        'branch': branch,
                        'quantity': quantity
                    }

                    # به روزرسانی موجودی انبار
                    try:
                        inventory_count = InventoryCount.objects.get(
                            product_name=product_name,
                            branch=branch
                        )
                        inventory_count.quantity += quantity
                        inventory_count.save()
                    except InventoryCount.DoesNotExist:
                        inventory_count = InventoryCount.objects.create(
                            product_name=product_name,
                            branch=branch,
                            quantity=quantity,
                            counter=request.user,
                            is_new=True
                        )
                else:
                    product_branch_totals[product_branch_key]['quantity'] += quantity
                    inventory_count = InventoryCount.objects.get(
                        product_name=product_name,
                        branch=branch
                    )
                    inventory_count.quantity += quantity
                    inventory_count.save()

            # تبدیل داده‌های موقت به فرمت مورد نیاز برای چاپ
            for key, data in product_branch_totals.items():
                product_name = data['product_name']
                branch = data['branch']
                quantity = data['quantity']

                if product_name not in print_data['items']:
                    print_data['items'][product_name] = {
                        'total': 0,
                        'branches': {}
                    }

                print_data['items'][product_name]['total'] += quantity

                if branch.name not in print_data['items'][product_name]['branches']:
                    print_data['items'][product_name]['branches'][branch.name] = 0
                print_data['items'][product_name]['branches'][branch.name] += quantity

            # ایجاد یا به روزرسانی سند مالی
            self.create_or_update_financial_document(invoice, invoice_items)

            # چاپ اطلاعات در کنسول
            self.print_invoice_data(print_data)

            # ذخیره اطلاعات برای استفاده در صفحه چاپ
            request.session['print_data'] = print_data

            return JsonResponse({
                'success': True,
                'message': 'اطلاعات انبار با موفقیت ثبت شد و مقادیر فاکتور به روز شدند',
                'print_url': '/account/print-invoice/'
            })

        except Exception as e:
            logger.error(f"Error storing invoice items: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})

    def update_invoice_remaining_quantities(self, invoice, print_data):
        """به روزرسانی مقادیر باقیمانده فاکتور بر اساس موجودی اضافه شده"""
        for invoice_item in invoice.items.all():
            product_name = invoice_item.product_name
            if product_name in print_data['items']:
                # محاسبه کل مقداری که به انبار اضافه شده
                total_stored = print_data['items'][product_name]['total']

                # به روزرسانی مقدار باقیمانده در فاکتور
                # فرض می‌کنیم فیلدی به نام remaining_quantity در InvoiceItem وجود دارد
                if hasattr(invoice_item, 'remaining_quantity'):
                    invoice_item.remaining_quantity = max(0, invoice_item.quantity - total_stored)
                    invoice_item.save()

    def create_or_update_financial_document(self, invoice, invoice_items):
        """ایجاد یا به روزرسانی سند مالی"""
        try:
            financial_doc, created = FinancialDocument.objects.get_or_create(
                invoice=invoice,
                defaults={
                    'document_date': datetime.now(),
                    'total_amount': Decimal('0'),
                    'paid_amount': Decimal('0'),
                    'status': 'unpaid'
                }
            )

            if not created:
                FinancialDocumentItem.objects.filter(document=financial_doc).delete()

            total_amount = Decimal('0')

            for item in invoice_items:
                price_before_discount = item.selling_price * item.quantity
                discount_amount = (price_before_discount * item.discount) / Decimal('100')
                final_price = price_before_discount - discount_amount

                FinancialDocumentItem.objects.create(
                    document=financial_doc,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount=item.discount,
                    total_price=final_price
                )

                total_amount += final_price

            financial_doc.total_amount = total_amount

            if financial_doc.paid_amount >= total_amount:
                financial_doc.status = 'settled'
            elif financial_doc.paid_amount > Decimal('0'):
                financial_doc.status = 'partially_paid'
            else:
                financial_doc.status = 'unpaid'

            financial_doc.save()

        except Exception as e:
            logger.error(f"Error creating financial document: {str(e)}")

    def print_invoice_data(self, print_data):
        """چاپ اطلاعات فاکتور در کنسول"""
        persian_print("=" * 50)
        persian_print(f"شماره فاکتور: {print_data['invoice_number']}")
        persian_print("=" * 50)

        for product_name, data in print_data['items'].items():
            persian_print(f"\nکالا: {product_name}")
            persian_print(f"جمع کل: {data['total']}")
            persian_print("توزیع بین شعب:")

            for branch_name, quantity in data['branches'].items():
                persian_print(f"  - {branch_name}: {quantity}")

        persian_print("\n" + "=" * 50)
        persian_print("پایان گزارش")

def print_invoice_view(request):
    """ویو برای نمایش صفحه چاپ فاکتور"""
    print_data = request.session.get('print_data', {})

    if not print_data:
        return HttpResponse("داده‌ای برای چاپ موجود نیست")

    # رندر کردن template با داده‌های فاکتور
    html_content = render_to_string('print_invoice.html', {
        'print_data': print_data
    })

    return HttpResponse(html_content)


import sys
import arabic_reshaper
from bidi.algorithm import get_display
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
import json
import logging
from decimal import Decimal
from datetime import datetime

# تنظیم encoding پیشفرض به UTF-8
if sys.stdout.encoding != 'UTF-8':
    sys.stdout.reconfigure(encoding='utf-8')

# تنظیمات reshaper برای فارسی
arabic_reshaper.configuration_for_arabic_letters = {
    'delete_harakat': False,
    'support_ligatures': True,
    'language': 'Farsi',
}


def persian_print(text):
    """تابع کمکی برای نمایش متن فارسی در کنسول"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        print(bidi_text)
    except Exception as e:
        # اگر خطایی رخ داد، متن را بدون تغییر چاپ کنید
        print(text)


# ---------------------------------------------------------------------------------------

def invoice_status(request, invoice_id):
    """نمایش وضعیت فاکتور و مقادیر باقیمانده"""
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        items = invoice.items.all()

        context = {
            'invoice': invoice,
            'items': items,
        }

        return render(request, 'invoice_status.html', context)

    except Invoice.DoesNotExist:
        return HttpResponse("فاکتور یافت نشد")


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from dashbord_app.models import Invoice, InvoiceItem
import json


@require_GET
def get_invoice_details(request):
    invoice_id = request.GET.get('invoice_id')
    try:
        invoice = Invoice.objects.get(id=invoice_id)

        # دریافت تمام آیتم‌های مربوط به این فاکتور
        items = invoice.items.all()

        # آماده کردن داده‌های آیتم‌ها برای ارسال به frontend
        items_data = []
        for item in items:
            items_data.append({
                'product_name': item.product_name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'selling_price': str(item.selling_price),
                'discount': str(item.discount),
                'item_number': item.item_number,
                'location': item.location,
                'remaining_quantity': item.remaining_quantity,
            })

        # آماده کردن داده‌های پاسخ
        data = {
            'success': True,
            'invoice': {
                'id': invoice.id,
                'serial_number': invoice.serial_number,
                'seller_name': str(invoice.seller),  # یا invoice.seller.name اگر مدل Froshande فیلد name دارد
                'date': invoice.jalali_date,
            },
            'items': items_data
        }

        return JsonResponse(data)

    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'فاکتور پیدا نشد'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})