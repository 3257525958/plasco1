

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
from .forms import FroshandeForm,InvoiceEditForm
logger = logging.getLogger(__name__)
# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse

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


def create_invoice(request):
    sellers = Froshande.objects.all()

    # دریافت زمان فعلی با منطقه زمانی
    now = timezone.localtime(timezone.now())

    # تبدیل به تاریخ شمسی
    jalali_date = jdatetime.datetime.fromgregorian(datetime=now)

    # تولید شماره سریال با فرمت YYMMDDHHMMSS
    serial_number = jalali_date.strftime('%y%m%d%H%M%S')
    serial_number_persian = convert_to_persian_digits(serial_number)

    # تبدیل تاریخ امروز به شمسی برای نمایش در فرم
    today_jalali = jalali_date.strftime('%Y/%m/%d')
    today_jalali = convert_to_persian_digits(today_jalali)

    if request.method == 'POST':
        # بررسی تأیید کاربر
        if 'confirmed' not in request.POST:
            # ذخیره داده‌ها به صورت صحیح در session
            request.session['invoice_data'] = {
                'seller': request.POST.get('seller'),
                'product_ids': request.POST.getlist('product_id[]'),
                'product_names': request.POST.getlist('product_name[]'),
                'quantities': request.POST.getlist('quantity[]'),
                'unit_prices': request.POST.getlist('unit_price[]'),
                'selling_prices': request.POST.getlist('selling_price[]'),
                'serial_number': serial_number,
            }
            return redirect('confirm_invoice')

        try:
            with transaction.atomic():
                # بازیابی داده‌ها از session
                invoice_data = request.session.get('invoice_data', {})
                if not invoice_data:
                    messages.error(request, 'داده‌های فاکتور یافت نشد. لطفاً دوباره تلاش کنید.')
                    return redirect('create_invoice')

                seller_id = invoice_data.get('seller')
                date = now.date()

                # ایجاد فاکتور با شماره سریال جدید
                invoice = Invoice.objects.create(
                    seller_id=seller_id,
                    date=date,
                    serial_number=serial_number
                )
                invoice.save()
                # اضافه کردن آیتم‌ها با استفاده از لیست‌ها
                product_ids = invoice_data.get('product_ids', [])
                product_names = invoice_data.get('product_names', [])
                quantities = invoice_data.get('quantities', [])
                unit_prices = invoice_data.get('unit_prices', [])
                selling_prices = invoice_data.get('selling_prices', [])
                for i in range(len(product_names)):
                    if product_names[i]:
                        product = None
                        if i < len(product_ids) and product_ids[i]:
                            try:
                                product = Product.objects.get(id=product_ids[i])
                            except Product.DoesNotExist:
                                logger.warning(f"محصول با شناسه {product_ids[i]} یافت نشد")
                                pass

                        # تبدیل مقادیر به انواع داده مناسب با مدیریت خطا
                        try:
                            quantity_val = int(quantities[i]) if i < len(quantities) else 1
                        except (ValueError, TypeError):
                            quantity_val = 1

                        try:
                            unit_price_val = Decimal(unit_prices[i]) if i < len(unit_prices) else Decimal(0)
                        except (ValueError, TypeError):
                            unit_price_val = Decimal(0)

                        try:
                            selling_price_val = Decimal(selling_prices[i]) if i < len(selling_prices) else Decimal(0)
                        except (ValueError, TypeError):
                            selling_price_val = Decimal(0)

                        # ایجاد آیتم فاکتور
                        item = InvoiceItem.objects.create(
                            invoice=invoice,
                            product=product,
                            product_name=product_names[i],
                            quantity=quantity_val,
                            unit_price=unit_price_val,
                            selling_price=selling_price_val,
                            item_number=i + 1  # این خط را اضافه کنید
                        )

                        # تنظیم شماره کالا
                        item.item_number = i + 1
                        item.save()

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


def search_sellers(request):
    query = request.GET.get('q', '')

    # تبدیل اعداد فارسی و عربی به انگلیسی
    query_english = convert_persian_arabic_to_english(query)

    sellers = Froshande.objects.filter(
        Q(name__icontains=query_english) |
        Q(family__icontains=query_english) |
        Q(store_name__icontains=query_english) |
        Q(mobile__icontains=query_english) |
        Q(sheba_number__icontains=query_english) |
        Q(card_number__icontains=query_english)
    )[:10]

    results = [
        {
            'id': seller.id,
            'text': f"{seller.name} {seller.family} - {seller.store_name or 'بدون نام فروشگاه'}",
            'mobile': seller.mobile,
            'sheba': seller.sheba_number,
            'card': seller.card_number,
            'name': seller.name,
            'family': seller.family,
            'store': seller.store_name
        }
        for seller in sellers
    ]

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
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib import messages
from .models import Invoice


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

def froshande_view(request):
    if request.method == 'POST':
        form = FroshandeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات فروشنده با موفقیت ثبت شد')
            return redirect('froshande')
        else:
            messages.error(request, 'خطا در ثبت اطلاعات. لطفا فرم را بررسی کنید')
    else:
        form = FroshandeForm()

    return render(request, 'froshande.html', {'form': form})


from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.utils.http import urlencode
from .models import Invoice


def print_settings(request):
    if request.method == 'POST':
        # ذخیره تنظیمات در session
        request.session['print_settings'] = {
            'columns': request.POST.get('columns', '3'),
            'page_alignment': request.POST.get('page_alignment', 'center'),
            'content_alignment': request.POST.get('content_alignment', 'center'),
            'vertical_gap': request.POST.get('vertical_gap', '5'),
            'horizontal_gap': request.POST.get('horizontal_gap', '5'),
            'barcode_scale': request.POST.get('barcode_scale', '90'),
            'content_spacing': request.POST.get('content_spacing', '5'),
            'font_family': request.POST.get('font_family', 'Vazirmatn'),
            'font_size': request.POST.get('font_size', '12'),
            'show_product_name': 'show_product_name' in request.POST,
            'show_price': 'show_price' in request.POST,
            'quantities': request.POST.getlist('quantity[]')
        }

        # هدایت به صفحه پیش‌نمایش چاپ
        invoice_id = request.POST.get('invoice_id')
        selected_items = request.POST.getlist('items')

        # ساخت URL برای صفحه پیش‌نمایش
        base_url = reverse('print_preview', kwargs={'invoice_id': invoice_id})
        query_string = urlencode({'items': selected_items}, doseq=True)
        return redirect(f"{base_url}?{query_string}")

    # کد GET request
    invoice_id = request.GET.get('invoice_id')
    items_ids = request.GET.getlist('items')
    invoice = get_object_or_404(Invoice, id=invoice_id)
    items = invoice.items.filter(id__in=items_ids)

    return render(request, 'print_settings.html', {
        'invoice': invoice,
        'items': items
    })


def print_preview(request, invoice_id):
    """صفحه پیش‌نمایش و چاپ نهایی"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    selected_items = request.GET.getlist('items')
    items = invoice.items.filter(id__in=selected_items)

    # دریافت تنظیمات از session
    settings = request.session.get('print_settings', {
        'columns': 3,
        'page_alignment': 'center',
        'content_alignment': 'center',
        'vertical_gap': 5,
        'horizontal_gap': 5,
        'barcode_scale': 90,
        'content_spacing': 5,
        'font_family': 'Vazirmatn',
        'font_size': 12,
        'show_product_name': True,
        'show_price': True,
        'quantities': ['1'] * len(items)
    })

    # ایجاد لیست نهایی آیتم‌ها با توجه به تعداد درخواستی هر کالا
    items_to_print = []
    for i, item in enumerate(items):
        quantity = int(settings['quantities'][i]) if i < len(settings['quantities']) else 1
        for _ in range(quantity):
            items_to_print.append(item)

    return render(request, 'print_preview.html', {
        'items': items_to_print,
        'settings': settings
    })


