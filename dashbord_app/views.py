

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from escpos.printer import Serial

from .models import Froshande, Invoice, InvoiceItem, Product
import jdatetime
import datetime
from decimal import Decimal
import logging
from .forms import FroshandeForm,InvoiceEditForm
logger = logging.getLogger(__name__)
# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib import messages
from .models import Froshande, Invoice, InvoiceItem, Product
import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import logging



# تغییر تابع generate_barcode_base64
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from .models import Froshande, Invoice, InvoiceItem, Product
import jdatetime
import datetime
from decimal import Decimal
import logging
from .forms import FroshandeForm, InvoiceEditForm
import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from django.urls import reverse
from django.utils.http import urlencode



from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from escpos.printer import Serial

from .models import Froshande, Invoice, InvoiceItem, Product
import jdatetime
import datetime
from decimal import Decimal
import logging
from .forms import FroshandeForm, InvoiceEditForm
logger = logging.getLogger(__name__)

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib import messages
from .models import Froshande, Invoice, InvoiceItem, Product
import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import logging


    # ----------------------------------------تولید و چاپ بارکد----------------------------------------


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlencode
import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import logging
from cantact_app.models import Branch
from account_app.models import Product,InventoryCount
from dashbord_app.models import Froshande, Invoice ,InvoiceItem
from dashbord_app.forms import FroshandeForm, InvoiceEditForm
import jdatetime
import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


from dashbord_app.forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlencode
import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import logging
import jdatetime
import datetime
from decimal import Decimal
import uuid



# توابع موجود قبلی را اینجا نگه دارید (create_invoice, search_sellers, etc.)
# ...
from django.http import JsonResponse
from account_app.models import InventoryCount
from account_app.utils import convert_persian_arabic_to_english

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def add_to_print_list(request):
    """افزودن آیتم به لیست چاپ"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')

            # دریافت آیتم از دیتابیس
            item = InventoryCount.objects.get(id=item_id)

            # ذخیره در session
            if 'selected_items' not in request.session:
                request.session['selected_items'] = []

            # بررسی تکراری نبودن آیتم
            if item_id not in request.session['selected_items']:
                request.session['selected_items'].append(item_id)
                request.session.modified = True  # این خط بسیار مهم است

                return JsonResponse({
                    'success': True,
                    'message': 'آیتم به لیست چاپ اضافه شد',
                    'count': len(request.session['selected_items'])
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'این آیتم قبلاً اضافه شده است'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا: {str(e)}'
            })
def quick_label_print_page(request):
    """نمایش صفحه اصلی جستجو برای چاپ لیبل"""
    # پاک کردن لیست انتخاب‌های قبلی از session
    if 'selected_items' in request.session:
        del request.session['selected_items']
    return render(request, 'quick_label_print.html')
def search_inventory_for_label(request):
    """جستجوی موجودی بر اساس نام کالا (API)"""
    query = request.GET.get('q', '')

    # اگر کوئری کمتر از 2 کاراکتر باشد، نتیجه خالی برگردان
    if len(query) < 2:
        return JsonResponse({'results': []})

    try:
        # جستجو در فیلد product_name
        inventory_items = InventoryCount.objects.filter(
            product_name__icontains=query
        ).select_related('branch')[:10]  # محدودیت نتایج

        results = []
        for item in inventory_items:
            results.append({
                'id': item.id,
                'product_name': item.product_name,
                'branch_name': item.branch.name,
                'quantity': item.quantity
            })

        return JsonResponse({'results': results})

    except Exception as e:
        logger.error(f"خطا در جستجوی موجودی: {str(e)}")
        return JsonResponse({'results': [], 'error': str(e)})
def get_print_list(request):
    """دریافت لیست آیتم‌های انتخاب شده برای چاپ"""
    selected_items = request.session.get('selected_items', [])
    items = []

    for item_id in selected_items:
        try:
            item = InventoryCount.objects.get(id=item_id)
            items.append({
                'id': item.id,
                'product_name': item.product_name,
                'branch_name': item.branch.name,
                'quantity': item.quantity
            })
        except InventoryCount.DoesNotExist:
            continue

    return JsonResponse({'items': items})
def clear_print_list(request):
    """پاک کردن لیست آیتم‌های انتخاب شده"""
    if 'selected_items' in request.session:
        del request.session['selected_items']
    return JsonResponse({'success': True})
def go_to_print_settings(request):
    """هدایت به صفحه تنظیمات چاپ"""
    selected_items = request.session.get('selected_items', [])

    if not selected_items:
        return JsonResponse({
            'success': False,
            'message': 'هیچ آیتمی برای چاپ انتخاب نشده است'
        })

    # استفاده از اولین آیتم از لیست
    first_item_id = selected_items[0]

    # هدایت به صفحه تنظیمات چاپ
    base_url = reverse('print_settings')
    query_string = urlencode({
        'type': 'inventory',
        'inventory_id': first_item_id,
        'quantity': len(selected_items)
    })

    return JsonResponse({
        'success': True,
        'redirect_url': f"{base_url}?{query_string}"
    })

# def quick_label_print_page(request):
#     """نمایش صفحه اصلی جستجو برای چاپ لیبل"""
#     return render(request, 'quick_label_print.html')

def generate_label_barcode(request):
    """تولید بارکد برای آیتم انتخاب شده"""
    if request.method == 'POST':
        inventory_id = request.POST.get('inventory_id')
        quantity = int(request.POST.get('quantity', 1))

        try:
            inventory = InventoryCount.objects.get(id=inventory_id)

            # هدایت به صفحه تنظیمات چاپ
            base_url = reverse('print_settings')
            query_string = urlencode({
                'type': 'inventory',
                'inventory_id': inventory_id,
                'quantity': quantity
            })

            return redirect(f"{base_url}?{query_string}")

        except InventoryCount.DoesNotExist:
            messages.error(request, 'آیتم انتخاب شده یافت نشد')
            return redirect('quick_label_print')

    return redirect('quick_label_print')


# def search_inventory_for_label(request):
#     """جستجوی موجودی بر اساس نام کالا (API)"""
#     query = request.GET.get('q', '')
#
#     # اگر کوئری کمتر از 2 کاراکتر باشد، نتیجه خالی برگردان
#     if len(query) < 2:
#         return JsonResponse({'results': []})
#
#     try:
#         # جستجو در فیلد product_name
#         inventory_items = InventoryCount.objects.filter(
#             Q(product_name__icontains=query)
#         ).select_related('branch')[:10]  # محدودیت نتایج
#
#         results = []
#         for item in inventory_items:
#             results.append({
#                 'id': item.id,
#                 'product_name': item.product_name,
#                 'branch_name': item.branch.name,
#                 'quantity': item.quantity
#             })
#
#         return JsonResponse({'results': results})
#
#     except Exception as e:
#         logger.error(f"خطا در جستجوی موجودی: {str(e)}")
#         return JsonResponse({'results': [], 'error': str(e)})# توابع جدید برای چاپ لیبل کالاها و شعب
def quick_label_print(request):
    """صفحه جستجو برای چاپ سریع لیبل"""
    return render(request, 'quick_label_print.html')
def search_products_for_label(request):
    """جستجوی کالاها برای چاپ لیبل"""
    query = request.GET.get('q', '')

    if query:
        # تبدیل اعداد فارسی و عربی به انگلیسی
        query_english = convert_persian_arabic_to_english(query)
        products = Product.objects.filter(name__icontains(query_english))[:10]
        results = [{'id': p.id, 'text': p.name} for p in products]
    else:
        results = []

    return JsonResponse({'results': results})


def search_branches_for_label(request):
    """جستجوی شعب برای چاپ لیبل"""
    query = request.GET.get('q', '')

    if query:
        # تبدیل اعداد فارسی و عربی به انگلیسی
        query_english = convert_persian_arabic_to_english(query)
        branches = Branch.objects.filter(
            Q(name__icontains(query_english)) |
            Q(address__icontains(query_english))
        )[:10]
        # حذف ارجاع به فیلد code و استفاده از name و address
        results = [{'id': b.id, 'text': f"{b.name} - {b.address[:30]}..."} for b in branches]
    else:
        results = []

    return JsonResponse({'results': results})
# به‌روزرسانی تابع print_settings برای پشتیبانی از هر دو نوع (فاکتور و موجودی)

def print_settings(request):
    """صفحه تنظیمات چاپ برای هر دو نوع فاکتور و موجودی"""
    print_type = request.GET.get('type', 'invoice')

    if print_type == 'inventory':
        # دریافت لیست آیتم‌های انتخاب شده از session
        selected_items_ids = request.session.get('selected_items', [])

        if not selected_items_ids:
            messages.error(request, 'هیچ آیتمی برای چاپ انتخاب نشده است')
            return redirect('quick_label_print')

        # دریافت اطلاعات آیتم‌های انتخاب شده از دیتابیس
        inventories = InventoryCount.objects.filter(id__in=selected_items_ids)

        if request.method == 'POST':
            # ذخیره تنظیمات در session
            quantities = request.POST.getlist('quantity[]')
            inventory_ids = request.POST.getlist('inventory_ids[]')

            request.session['print_settings'] = {
                'barcodes_per_label': request.POST.get('barcodes_per_label', '1'),
                'content_alignment': request.POST.get('content_alignment', 'center'),
                'vertical_gap': request.POST.get('vertical_gap', '5'),
                'inner_gap': request.POST.get('inner_gap', '5'),
                'barcode_scale': request.POST.get('barcode_scale', '90'),
                'content_spacing': request.POST.get('content_spacing', '5'),
                'font_family': request.POST.get('font_family', 'Vazirmatn'),
                'font_size': request.POST.get('font_size', '12'),
                'show_product_name': 'show_product_name' in request.POST,
                'show_price': 'show_price' in request.POST,
                'quantities': quantities,  # ذخیره تعدادهای وارد شده برای هر آیتم
                'inventory_ids': inventory_ids,  # ذخیره شناسه‌های آیتم‌ها
                'module_width': request.POST.get('module_width', '0.2'),
                'module_height': request.POST.get('module_height', '15')
            }

            # استفاده از URL مناسب برای inventory
            base_url = reverse('print_preview_inventory')
            return redirect(f"{base_url}")

        else:
            # برای درخواست‌های GET
            settings = request.session.get('print_settings', {})
            return render(request, 'print_settings.html', {
                'inventories': inventories,  # ارسال لیست آیتم‌ها به تمپلیت
                'settings': settings,
                'print_type': 'inventory'
            })

    else:
        # پردازش چاپ فاکتور (بدون تغییر)
        invoice_id = request.GET.get('invoice_id')
        items_ids = request.GET.getlist('items')
        invoice = get_object_or_404(Invoice, id=invoice_id)
        items = invoice.items.filter(id__in=items_ids)

        if request.method == 'POST':
            # ذخیره تنظیمات در session
            request.session['print_settings'] = {
                'barcodes_per_label': request.POST.get('barcodes_per_label', '2'),
                'content_alignment': request.POST.get('content_alignment', 'center'),
                'vertical_gap': request.POST.get('vertical_gap', '5'),
                'inner_gap': request.POST.get('inner_gap', '5'),
                'barcode_scale': request.POST.get('barcode_scale', '90'),
                'content_spacing': request.POST.get('content_spacing', '5'),
                'font_family': request.POST.get('font_family', 'Vazirmatn'),
                'font_size': request.POST.get('font_size', '12'),
                'show_product_name': 'show_product_name' in request.POST,
                'show_price': 'show_price' in request.POST,
                'quantities': request.POST.getlist('quantity[]'),
                'module_width': request.POST.get('module_width', '0.2'),
                'module_height': request.POST.get('module_height', '15')
            }

            # استفاده از URL مناسب برای فاکتور
            base_url = reverse('print_preview_invoice', kwargs={'invoice_id': invoice_id})
            query_string = urlencode({'items': items_ids}, doseq=True)

            return redirect(f"{base_url}?{query_string}")

        else:
            # برای درخواست‌های GET
            settings = request.session.get('print_settings', {})
            return render(request, 'print_settings.html', {
                'invoice': invoice,
                'items': items,
                'settings': settings,
                'print_type': 'invoice'
            })


def print_preview(request, invoice_id=None):
    """صفحه پیش‌نمایش و چاپ نهایی برای هر دو نوع"""
    print_type = request.GET.get('type', 'invoice')

    if print_type == 'inventory' or invoice_id is None:
        # دریافت تنظیمات از session
        settings = request.session.get('print_settings', {
            'barcodes_per_label': '1',
            'content_alignment': 'center',
            'vertical_gap': '5',
            'inner_gap': '5',
            'barcode_scale': '90',
            'content_spacing': '5',
            'font_family': 'Vazirmatn',
            'font_size': '12',
            'show_product_name': True,
            'show_price': False,
            'module_width': '0.2',
            'module_height': '15'
        })

        # دریافت لیست آیتم‌ها و تعدادهای مورد نظر
        quantities = settings.get('quantities', [])
        inventory_ids = settings.get('inventory_ids', [])

        # تعداد بارکد در هر لیبل
        try:
            barcodes_per_label = int(settings.get('barcodes_per_label', '1'))
        except (ValueError, TypeError):
            barcodes_per_label = 1

        # ایجاد لیست نهایی لیبل‌ها
        labels_to_print = []
        current_label = []

        # ساخت لیست آیتم‌ها با تعداد درخواستی
        items_to_print = []
        for i, inventory_id in enumerate(inventory_ids):
            try:
                inventory = InventoryCount.objects.get(id=inventory_id)
                quantity = int(quantities[i]) if i < len(quantities) else 1

                for j in range(quantity):
                    # تولید بارکد برای هر آیتم
                    barcode_base64 = generate_barcode_base64(
                        inventory.barcode_data,
                        module_width=float(settings.get('module_width', 0.2)),
                        module_height=float(settings.get('module_height', 15))
                    )
                    items_to_print.append({
                        'product_name': inventory.product_name,
                        'branch_name': inventory.branch.name,
                        'barcode_base64': barcode_base64
                    })
            except InventoryCount.DoesNotExist:
                continue

        # گروه‌بندی آیتم‌ها در لیبل‌ها
        for i, item in enumerate(items_to_print):
            current_label.append(item)

            # اگر لیبل پر شد یا به آخر رسیدیم
            if len(current_label) == barcodes_per_label or i == len(items_to_print) - 1:
                labels_to_print.append(current_label)
                current_label = []

        return render(request, 'print_preview.html', {
            'labels': labels_to_print,
            'settings': settings,
            'print_type': 'inventory'
        })

    else:
        # پردازش پیش‌نمایش فاکتور (بدون تغییر)
        invoice = get_object_or_404(Invoice, id=invoice_id)
        selected_items = request.GET.getlist('items')
        items = invoice.items.filter(id__in=selected_items)

        # دریافت تنظیمات از session
        settings = request.session.get('print_settings', {
            'barcodes_per_label': '2',
            'content_alignment': 'center',
            'vertical_gap': '5',
            'inner_gap': '5',
            'barcode_scale': '90',
            'content_spacing': '5',
            'font_family': 'Vazirmatn',
            'font_size': '12',
            'show_product_name': True,
            'show_price': True,
            'module_width': '0.2',
            'module_height': '15'
        })

        # تعداد بارکد در هر لیبل
        try:
            barcodes_per_label = int(settings.get('barcodes_per_label', '2'))
        except (ValueError, TypeError):
            barcodes_per_label = 2

        # ایجاد لیست نهایی لیبل‌ها (هر لیبل شامل چندین آیتم)
        labels_to_print = []
        current_label = []

        # ساخت لیست آیتم‌ها با تعداد درخواستی
        items_to_print = []
        for i, item in enumerate(items):
            quantity = int(settings['quantities'][i]) if i < len(settings['quantities']) else 1
            for _ in range(quantity):
                # تولید بارکد برای هر آیتم
                barcode_value = f"{invoice.serial_number}-{item.id}"
                barcode_base64 = generate_barcode_base64(
                    barcode_value,
                    module_width=float(settings.get('module_width', 0.2)),
                    module_height=float(settings.get('module_height', 15))
                )
                items_to_print.append({
                    'product_name': item.product_name,
                    'selling_price': item.selling_price,
                    'barcode_base64': barcode_base64
                })

        # گروه‌بندی آیتم‌ها در لیبل‌ها
        for i, item in enumerate(items_to_print):
            current_label.append(item)

            # اگر لیبل پر شد یا به آخر رسیدیم
            if len(current_label) == barcodes_per_label or i == len(items_to_print) - 1:
                labels_to_print.append(current_label)
                current_label = []

        return render(request, 'print_preview.html', {
            'labels': labels_to_print,
            'settings': settings,
            'invoice': invoice,
            'print_type': 'invoice'
        })

# به‌روزرسانی تابع print_preview برای پشتیبانی از هر دو نوع


# def print_preview(request, invoice_id=None):
#     """صفحه پیش‌نمایش و چاپ نهایی برای هر دو نوع"""
#     print_type = request.GET.get('type', 'invoice')
#
#     if print_type == 'inventory' or invoice_id is None:
#         # پردازش پیش‌نمایش لیبل موجودی
#         inventory_id = request.GET.get('inventory_id')
#         quantity = int(request.GET.get('quantity', 1))
#
#         if not inventory_id:
#             messages.error(request, 'شناسه موجودی یافت نشد')
#             return redirect('quick_label_print')
#
#         inventory = get_object_or_404(InventoryCount, id=inventory_id)
#
#         # دریافت تنظیمات از session
#         settings = request.session.get('print_settings', {
#             'barcodes_per_label': '1',
#             'content_alignment': 'center',
#             'vertical_gap': '5',
#             'inner_gap': '5',
#             'barcode_scale': '90',
#             'content_spacing': '5',
#             'font_family': 'Vazirmatn',
#             'font_size': '12',
#             'show_product_name': True,
#             'show_price': False,
#             'quantity': quantity,
#             'module_width': '0.2',
#             'module_height': '15'
#         })
#
#         # تعداد بارکد در هر لیبل
#         try:
#             barcodes_per_label = int(settings.get('barcodes_per_label', '1'))
#         except (ValueError, TypeError):
#             barcodes_per_label = 1
#
#         # ایجاد لیست نهایی لیبل‌ها
#         labels_to_print = []
#         current_label = []
#
#         # ساخت لیست آیتم‌ها با تعداد درخواستی
#         items_to_print = []
#         for i in range(quantity):
#             # تولید بارکد برای هر آیتم
#             barcode_base64 = generate_barcode_base64(
#                 inventory.barcode_data,
#                 module_width=float(settings.get('module_width', 0.2)),
#                 module_height=float(settings.get('module_height', 15))
#             )
#             items_to_print.append({
#                 'product_name': inventory.product_name,
#                 'branch_name': inventory.branch.name,
#                 'barcode_base64': barcode_base64
#             })
#
#         # گروه‌بندی آیتم‌ها در لیبل‌ها
#         for i, item in enumerate(items_to_print):
#             current_label.append(item)
#
#             # اگر لیبل پر شد یا به آخر رسیدیم
#             if len(current_label) == barcodes_per_label or i == len(items_to_print) - 1:
#                 labels_to_print.append(current_label)
#                 current_label = []
#
#         return render(request, 'print_preview.html', {
#             'labels': labels_to_print,
#             'settings': settings,
#             'inventory': inventory,
#             'print_type': 'inventory'
#         })
#
#     else:
#         # پردازش پیش‌نمایش فاکتور
#         invoice = get_object_or_404(Invoice, id=invoice_id)
#         selected_items = request.GET.getlist('items')
#         items = invoice.items.filter(id__in=selected_items)
#
#         # دریافت تنظیمات از session
#         settings = request.session.get('print_settings', {
#             'barcodes_per_label': '2',
#             'content_alignment': 'center',
#             'vertical_gap': '5',
#             'inner_gap': '5',
#             'barcode_scale': '90',
#             'content_spacing': '5',
#             'font_family': 'Vazirmatn',
#             'font_size': '12',
#             'show_product_name': True,
#             'show_price': True,
#             'module_width': '0.2',
#             'module_height': '15'
#         })
#
#         # تعداد بارکد در هر لیبل
#         try:
#             barcodes_per_label = int(settings.get('barcodes_per_label', '2'))
#         except (ValueError, TypeError):
#             barcodes_per_label = 2
#
#         # ایجاد لیست نهایی لیبل‌ها (هر لیبل شامل چندین آیتم)
#         labels_to_print = []
#         current_label = []
#
#         # ساخت لیست آیتم‌ها با تعداد درخواستی
#         items_to_print = []
#         for i, item in enumerate(items):
#             quantity = int(settings['quantities'][i]) if i < len(settings['quantities']) else 1
#             for _ in range(quantity):
#                 # تولید بارکد برای هر آیتم
#                 barcode_value = f"{invoice.serial_number}-{item.id}"
#                 barcode_base64 = generate_barcode_base64(
#                     barcode_value,
#                     module_width=float(settings.get('module_width', 0.2)),
#                     module_height=float(settings.get('module_height', 15))
#                 )
#                 items_to_print.append({
#                     'product_name': item.product_name,
#                     'selling_price': item.selling_price,
#                     'barcode_base64': barcode_base64
#                 })
#
#         # گروه‌بندی آیتم‌ها در لیبل‌ها
#         for i, item in enumerate(items_to_print):
#             current_label.append(item)
#
#             # اگر لیبل پر شد یا به آخر رسیدیم
#             if len(current_label) == barcodes_per_label or i == len(items_to_print) - 1:
#                 labels_to_print.append(current_label)
#                 current_label = []
#
#         return render(request, 'print_preview.html', {
#             'labels': labels_to_print,
#             'settings': settings,
#             'invoice': invoice,
#             'print_type': 'invoice'
#         })



def print_label(request, label_type):
    # دریافت تنظیمات چاپ برای این نوع لیبل
    print_setting = get_object_or_404(LabelPrintSetting, label_type=label_type, is_active=True)

    # تعداد چاپ از تنظیمات دریافت می‌شود
    copies = print_setting.copies_count

    # منطق چاپ لیبل
    for i in range(copies):
        # چاپ لیبل
        pass

    return HttpResponse("لیبل‌ها با موفقیت چاپ شدند")
# تابع کمکی برای تولید بارکد
def generate_barcode_base64(barcode_value, module_width=0.2, module_height=15):
    """تولید بارکد به صورت base64 با تنظیم عرض و ارتفاع میله‌ها"""
    try:
        # تولید بارکد استاندارد Code128
        code128 = barcode.get('code128', barcode_value, writer=ImageWriter())

        # تنظیمات برای بارکد
        options = {
            'module_width': float(module_width),  # عرض هر میله بارکد
            'module_height': float(module_height),  # ارتفاع بارکد
            'quiet_zone': 5,  # فضای خالی اطراف بارکد
            'write_text': False  # عدم نمایش متن زیر بارکد
        }

        # ایجاد بافر برای ذخیره موقت
        buffer = BytesIO()
        code128.write(buffer, options=options)
        buffer.seek(0)

        # تبدیل به base64
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{image_base64}"

    except Exception as e:
        logger.error(f"Error generating barcode: {str(e)}")
        return None
# توابع کمکی برای تبدیل اعداد
def convert_persian_arabic_to_english(text):
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    arabic_numbers = '٠١٢٣٤٥٦٧٨٩'
    english_numbers = '0123456789'
    translation_table = str.maketrans(persian_numbers + arabic_numbers, english_numbers * 2)
    return text.translate(translation_table)
def convert_to_persian_digits(text):
    """تبدیل اعداد انگلیسی به فارسی"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    return ''.join(persian_digits[int(d)] if d.isdigit() else d for d in str(text))
# توابع موجود قبلی را اینجا نگه دارید (create_invoice, search_sellers, etc.)


# -----------------------------------------------------------------------------------------------



def create_invoice(request):
    sellers = Froshande.objects.all()
    now = timezone.localtime(timezone.now())
    jalali_date = jdatetime.datetime.fromgregorian(datetime=now)
    serial_number = jalali_date.strftime('%y%m%d%H%M%S')
    serial_number_persian = convert_to_persian_digits(serial_number)
    today_jalali = jalali_date.strftime('%Y/%m/%d')
    today_jalali = convert_to_persian_digits(today_jalali)

    if request.method == 'POST':
        if 'confirmed' not in request.POST:
            request.session['invoice_data'] = {
                'seller': request.POST.get('seller'),
                'product_ids': request.POST.getlist('product_id[]'),
                'product_names': request.POST.getlist('product_name[]'),
                'quantities': request.POST.getlist('quantity[]'),
                'unit_prices': request.POST.getlist('unit_price[]'),
                'discounts': request.POST.getlist('discount[]'),
                'serial_number': serial_number,
            }
            return redirect('confirm_invoice')

        try:
            with transaction.atomic():
                invoice_data = request.session.get('invoice_data', {})
                if not invoice_data:
                    messages.error(request, 'داده‌های فاکتور یافت نشد. لطفاً دوباره تلاش کنید.')
                    return redirect('create_invoice')

                seller_id = invoice_data.get('seller')
                date = now.date()

                # ایجاد فاکتور
                invoice = Invoice.objects.create(
                    seller_id=seller_id,
                    date=date,
                    serial_number=serial_number
                )

                # محاسبه جمع‌های فاکتور
                total_amount = Decimal(0)
                total_discount = Decimal(0)

                # اضافه کردن آیتم‌ها
                product_ids = invoice_data.get('product_ids', [])
                product_names = invoice_data.get('product_names', [])
                quantities = invoice_data.get('quantities', [])
                unit_prices = invoice_data.get('unit_prices', [])
                discounts = invoice_data.get('discounts', [])

                for i in range(len(product_names)):
                    if product_names[i]:
                        product = None
                        if i < len(product_ids) and product_ids[i]:
                            try:
                                product = Product.objects.get(id=product_ids[i])
                            except Product.DoesNotExist:
                                logger.warning(f"محصول با شناسه {product_ids[i]} یافت نشد")
                                pass

                        try:
                            quantity_val = int(quantities[i]) if i < len(quantities) else 1
                        except (ValueError, TypeError):
                            quantity_val = 1

                        try:
                            unit_price_val = Decimal(unit_prices[i]) if i < len(unit_prices) else Decimal(0)
                        except (ValueError, TypeError):
                            unit_price_val = Decimal(0)

                        try:
                            discount_val = Decimal(discounts[i]) if i < len(discounts) else Decimal(0)
                        except (ValueError, TypeError):
                            discount_val = Decimal(0)

                        # ایجاد آیتم فاکتور
                        item = InvoiceItem.objects.create(
                            invoice=invoice,
                            product=product,
                            product_name=product_names[i],
                            quantity=quantity_val,
                            unit_price=unit_price_val,
                            discount=discount_val,
                            item_number=i + 1
                        )

                        # محاسبه جمع‌ها
                        total_amount += quantity_val * unit_price_val
                        total_discount += discount_val

                # به روزرسانی فاکتور با مقادیر محاسبه شده
                invoice.total_amount = total_amount
                invoice.total_discount = total_discount
                invoice.total_payable = total_amount - total_discount
                invoice.save()

                # حذف داده‌های موقت از session
                if 'invoice_data' in request.session:
                    del request.session['invoice_data']

                messages.success(request, 'فاکتور با موفقیت ثبت شد')
                return redirect('invoice_detail', invoice_id=invoice.id)

        except Exception as e:
            logger.exception("Error in create_invoice")
            return render(request, 'invoice_form.html', {
                'sellers': sellers,
                'today_jalali': today_jalali,
                'serial_number': serial_number_persian,
                'error_message': f'خطا در ایجاد فاکتور: لطفاً داده‌ها را بررسی کنید'
            })

    return render(request, 'invoice_form.html', {
        'sellers': sellers,
        'today_jalali': today_jalali,
        'serial_number': serial_number_persian
    })
from django.db.models import Q
from django.http import JsonResponse
from .models import Froshande, ContactNumber, BankAccount


# views.py
def search_sellers(request):
    query = request.GET.get('q', '')

    # تبدیل اعداد فارسی و عربی به انگلیسی
    query_english = convert_persian_arabic_to_english(query)

    # جستجو با prefetch_related برای بهینه‌سازی
    sellers = Froshande.objects.filter(
        Q(name__icontains=query_english) |
        Q(family__icontains=query_english) |
        Q(store_name__icontains=query_english)
    ).prefetch_related(
        'contact_numbers',
        'bank_accounts'
    )[:10]

    results = []
    for seller in sellers:
        # پیدا کردن شماره موبایل اصلی
        mobile = None
        for contact in seller.contact_numbers.all():
            if contact.contact_type == 'mobile' and contact.is_primary:
                mobile = contact.number
                break

        # اگر شماره موبایل اصلی پیدا نشد، اولین شماره موبایل را برمی‌گردانیم
        if not mobile:
            for contact in seller.contact_numbers.all():
                if contact.contact_type == 'mobile':
                    mobile = contact.number
                    break

        # پیدا کردن اطلاعات بانکی اصلی
        sheba = None
        card = None
        for bank in seller.bank_accounts.all():
            if bank.is_primary:
                sheba = bank.sheba_number
                card = bank.card_number
                break

        results.append({
            'id': seller.id,
            'text': f"{seller.name} {seller.family} - {seller.store_name or 'بدون نام فروشگاه'}",
            'mobile': mobile or '---',
            'sheba': sheba or '---',
            'card': card or '---',
            'name': seller.name,
            'family': seller.family,
            'store': seller.store_name or 'بدون نام فروشگاه',
            'address': seller.address or '---'  # اضافه کردن آدرس
        })
    return JsonResponse({'results': results})

def search_products(request):
    query = request.GET.get('q', '')

    # تبدیل اعداد فارسی و عربی به انگلیسی
    query_english = convert_persian_arabic_to_english(query)

    # جستجو فقط در مدل InvoiceItem برای نام‌های کالا
    items = InvoiceItem.objects.filter(
        product_name__icontains=query_english
    ).values('product_name').distinct().order_by('product_name')[:10]

    # ساخت نتایج
    results = [
        {
            'id': None,  # چون از مدل Product نیست، ID نداریم
            'text': item['product_name'],
            'type': 'invoice_item'
        }
        for item in items
    ]

    return JsonResponse({'results': results})

def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # محاسبه جمع کل فاکتور
    total = sum(item.total_price for item in invoice.items.all())

    # تبدیل تاریخ فاکتور به شمسی
    invoice_date = invoice.date
    invoice_jalali = jdatetime.datetime.fromgregorian(
        year=invoice_date.year,
        month=invoice_date.month,
        day=invoice_date.day
    ).strftime('%Y/%m/%d')
    invoice_jalali = convert_to_persian_digits(invoice_jalali)

    # تاریخ چاپ فعلی به شمسی
    now = timezone.now()
    print_date = jdatetime.datetime.fromgregorian(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute
    ).strftime('%Y/%m/%d %H:%M')
    print_date = convert_to_persian_digits(print_date)

    return render(request, 'invoice_detail.html', {
        'invoice': invoice,
        'total': total,
        'invoice_jalali': invoice_jalali,
        'print_date': print_date
    })


def confirm_invoice(request):
    if request.method == 'POST':
        if 'confirmed' in request.POST:
            # فراخوانی تابع ایجاد فاکتور
            return create_invoice(request)
        else:
            # حذف داده‌های موقت از session
            if 'invoice_data' in request.session:
                del request.session['invoice_data']
            return redirect('create_invoice')

    # نمایش صفحه تأیید
    invoice_data = request.session.get('invoice_data', {})
    seller_id = invoice_data.get('seller')
    seller = get_object_or_404(Froshande, id=seller_id) if seller_id else None
    items_count = len(invoice_data.get('product_names', []))

    return render(request, 'confirm_invoice.html', {
        'seller': seller,
        'items_count': items_count
    })


def search_invoices(request):
    """جستجوی فاکتورها بر اساس معیارهای مختلف"""
    query = request.GET.get('q', '')

    # فقط در صورت وجود عبارت جستجو، فاکتورها را جستجو کنید
    if query:
        # تبدیل اعداد فارسی و عربی به انگلیسی
        query_english = convert_persian_arabic_to_english(query)

        # ایجاد کوئری داینامیک برای جستجو
        invoices = Invoice.objects.filter(
            Q(serial_number__icontains=query_english) |
            Q(seller__name__icontains=query_english) |
            Q(seller__family__icontains=query_english) |
            Q(seller__store_name__icontains=query_english) |
            Q(seller__mobile__icontains=query_english) |
            Q(seller__card_number__icontains=query_english) |
            Q(seller__sheba_number__icontains=query_english)
        ).distinct().order_by('-date')[:20]
    else:
        invoices = None  # قبل از جستجو هیچ فاکتوری نمایش داده نشود

    return render(request, 'search_invoices.html', {
        'invoices': invoices,
        'query': query
    })



def edit_invoice(request, invoice_id):
    """ویرایش فاکتور با سیستم هشدار تغییرات"""
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        # اگر دکمه ذخیره تغییرات زده شده باشد
        if 'save' in request.POST:
            form = InvoiceEditForm(request.POST, instance=invoice)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        form.save()

                        # ذخیره آیتم‌ها
                        for item in invoice.items.all():
                            item_id = str(item.id)

                            # دریافت مقادیر جدید
                            product_name = request.POST.get(f'product_name_{item_id}')
                            unit_price = request.POST.get(f'unit_price_{item_id}')
                            selling_price = request.POST.get(f'selling_price_{item_id}')
                            quantity = request.POST.get(f'quantity_{item_id}')
                            # دریافت مقادیر جدید
                            discount = request.POST.get(f'discount_{item_id}')
                            location = request.POST.get(f'location_{item_id}')

                            # اعتبارسنجی و تبدیل انواع داده
                            if product_name:
                                item.product_name = product_name

                            if unit_price:
                                try:
                                    item.unit_price = Decimal(unit_price)
                                except (ValueError, TypeError):
                                    pass

                            if selling_price:
                                try:
                                    item.selling_price = Decimal(selling_price)
                                except (ValueError, TypeError):
                                    pass

                            if quantity:
                                try:
                                    item.quantity = int(quantity)
                                except (ValueError, TypeError):
                                    pass

                            # اعتبارسنجی فیلدهای جدید
                            if discount:
                                try:
                                    item.discount = Decimal(discount)
                                except (ValueError, TypeError):
                                    pass

                            if location:
                                item.location = location

                            item.save()

                        messages.success(request, 'تغییرات فاکتور با موفقیت ثبت شد')
                        return redirect('edit_invoice', invoice_id=invoice.id)

                except Exception as e:
                    logger.error(f"Error saving invoice changes: {str(e)}")
                    messages.error(request, f'خطا در ذخیره تغییرات: {str(e)}')
            else:
                messages.error(request, 'خطا در فرم فروشنده. لطفاً داده‌ها را بررسی کنید')

        # درخواست چاپ لیبل
        elif 'print' in request.POST:
            selected_items = request.POST.getlist('selected_items')
            if not selected_items:
                messages.warning(request, 'هیچ کالایی برای چاپ انتخاب نشده است')
                return redirect('edit_invoice', invoice_id=invoice.id)

            base_url = reverse('print_settings')
            query_string = urlencode({
                'invoice_id': invoice_id,
                'items': selected_items
            }, doseq=True)
            return redirect(f"{base_url}?{query_string}")

    else:
        form = InvoiceEditForm(instance=invoice)

    return render(request, 'edit_invoice.html', {
        'invoice': invoice,
        'form': form,
    })



def print_labels(request, invoice_id):
    """هدایت به صفحه تنظیمات چاپ"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    selected_items = request.GET.getlist('items')

    if not selected_items:
        messages.warning(request, 'هیچ کالایی برای چاپ انتخاب نشده است')
        return redirect('edit_invoice', invoice_id=invoice_id)

    # هدایت به صفحه تنظیمات چاپ
    base_url = reverse('print_settings')
    query_string = urlencode({
        'invoice_id': invoice_id,
        'items': selected_items
    }, doseq=True)

    return redirect(f"{base_url}?{query_string}")


#
# -----------------------------------------------------------------------------------------
import serial

def usb_view(request):
    ser = serial.Serial('COM3', 9600)  # پورت COM دستگاه را تنظیم کنید
    ser.write(b"\x1B\x40")  # دستور فعال‌سازی ESC/POS
    ser.close()
    printer = Serial(devfile='COM3', baudrate=9600)
    printer.text("قیمت: 50,000 تومان\n")
    printer.cut()
    return render(request, 'froshande.html', {'printer': printer})
# ------------------------فرو شنده--------------------------------------------------------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory, inlineformset_factory
from django.contrib import messages
from .models import Froshande, ContactNumber, BankAccount
from .forms import FroshandeForm, ContactNumberForm, BankAccountForm
import re


# def is_persian(text):
#     return bool(re.match(r'^[\u0600-\u06FF\s]+$', text))


def froshande_view(request):
    if request.method == 'POST':
        for field in ['name', 'family', 'store_name', 'address']:
            if field in request.POST and request.POST[field]:
                if not is_persian(request.POST[field]):
                    messages.error(request, 'لطفاً فقط از حروف فارسی استفاده کنید.')
                    return render(request, 'froshande.html', {'form': FroshandeForm(request.POST)})

        form = FroshandeForm(request.POST)
        if form.is_valid():
            froshande = form.save()
            messages.success(request, 'اطلاعات فروشنده با موفقیت ثبت شد')
            return redirect('froshande_accounts', froshande_id=froshande.id)
        else:
            messages.error(request, 'خطا در ثبت اطلاعات. لطفا فرم را بررسی کنید')
    else:
        form = FroshandeForm()

    return render(request, 'froshande.html', {'form': form})


def froshande_accounts_view(request, froshande_id):
    froshande = get_object_or_404(Froshande, id=froshande_id)

    # استفاده از inlineformset_factory برای مدیریت بهتر روابط
    ContactFormSet = inlineformset_factory(
        Froshande,
        ContactNumber,
        form=ContactNumberForm,
        extra=1,
        can_delete=True
    )

    BankFormSet = inlineformset_factory(
        Froshande,
        BankAccount,
        form=BankAccountForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        contact_formset = ContactFormSet(request.POST, instance=froshande, prefix='contacts')
        bank_formset = BankFormSet(request.POST, instance=froshande, prefix='banks')

        if contact_formset.is_valid() and bank_formset.is_valid():
            # ذخیره فرم‌ها
            contact_formset.save()
            bank_formset.save()

            messages.success(request, 'اطلاعات تماس و حساب بانکی با موفقیت ثبت شد')
            return redirect('froshande_list')  # تغییر به مسیر مناسب

        else:
            # نمایش خطاهای فرم
            messages.error(request, 'لطفاً خطاهای زیر را بررسی کنید:')
            for form in contact_formset:
                if form.errors:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'خطا در شماره تماس: {error}')

            for form in bank_formset:
                if form.errors:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'خطا در حساب بانکی: {error}')

    else:
        contact_formset = ContactFormSet(instance=froshande, prefix='contacts')
        bank_formset = BankFormSet(instance=froshande, prefix='banks')

    context = {
        'froshande': froshande,
        'contact_formset': contact_formset,
        'bank_formset': bank_formset,
    }

    return render(request, 'froshande_accounts.html', context)

# -------------------------------------------ویرایش فروشنده------------------------------------------------------------------
def froshande_edit_view(request, froshande_id):
    froshande = get_object_or_404(Froshande, id=froshande_id)

    if request.method == 'POST':
        form = FroshandeForm(request.POST, instance=froshande)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات فروشنده با موفقیت ویرایش شد')
            return redirect('froshande_accounts', froshande_id=froshande.id)
    else:
        form = FroshandeForm(instance=froshande)

    return render(request, 'froshande_edit.html', {'form': form, 'froshande': froshande})


def froshande_list_view(request):
    froshandes = Froshande.objects.all().prefetch_related('contact_numbers', 'bank_accounts')
    return render(request, 'froshande_list.html', {'froshandes': froshandes})



# -------------------------حذف فروشنده----------------------------------------------------------------------------------


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse


def froshande_delete_view(request, froshande_id):
    froshande = get_object_or_404(Froshande, id=froshande_id)

    if request.method == 'POST':
        # حذف فروشنده و تمام اطلاعات مرتبط
        froshande_name = f"{froshande.name} {froshande.family}"
        froshande.delete()

        messages.success(request, f'فروشنده "{froshande_name}" با موفقیت حذف شد')
        return redirect('froshande_list')

    return JsonResponse({'error': 'متد غیرمجاز'}, status=405)


def froshande_delete_ajax(request, froshande_id):
    # برای حذف با درخواست AJAX
    if request.method == 'POST' and request.is_ajax():
        froshande = get_object_or_404(Froshande, id=froshande_id)
        froshande_name = f"{froshande.name} {froshande.family}"
        froshande.delete()

        return JsonResponse({
            'success': True,
            'message': f'فروشنده "{froshande_name}" با موفقیت حذف شد'
        })

    return JsonResponse({'error': 'متد غیرمجاز'}, status=405)







# ------------پرینت لیبل-------------------------

from django.shortcuts import get_object_or_404


def print_label(request, label_type):
    # دریافت تنظیمات چاپ برای این نوع لیبل
    print_setting = get_object_or_404(LabelPrintSetting, label_type=label_type, is_active=True)

    # تعداد چاپ از تنظیمات دریافت می‌شود
    copies = print_setting.copies_count

    # منطق چاپ لیبل
    for i in range(copies):
        # چاپ لیبل
        pass

    return HttpResponse("لیبل‌ها با موفقیت چاپ شدند")
