import socket
import json
import re
import time

from django.contrib.sites import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.utils import timezone
from decimal import Decimal
import jdatetime
from datetime import datetime

from account_app.models import InventoryCount, Branch, ProductPricing
from .models import Invoicefrosh, InvoiceItemfrosh, POSDevice, CheckPayment, CreditPayment
from .forms import BranchSelectionForm, POSDeviceForm, CheckPaymentForm, CreditPaymentForm


import jdatetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.utils import timezone
from decimal import Decimal
import json
from datetime import datetime

from account_app.models import InventoryCount, Branch, ProductPricing
from .models import Invoicefrosh, InvoiceItemfrosh, POSDevice, CheckPayment, CreditPayment
from .forms import BranchSelectionForm, POSDeviceForm, CheckPaymentForm, CreditPaymentForm

import jdatetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.utils import timezone
from decimal import Decimal
import json
from datetime import datetime

from account_app.models import InventoryCount, Branch, ProductPricing
from .models import Invoicefrosh, InvoiceItemfrosh, POSDevice, CheckPayment, CreditPayment
from .forms import BranchSelectionForm, POSDeviceForm, CheckPaymentForm, CreditPaymentForm

# مپینگ شعبه به سرویس واسط
BRIDGE_SERVICE_MAPPING = {
    # branch_id: "bridge_service_ip"
    # مثال - اینها را با IPهای واقعی پر کنید:
    1: "192.168.1.172",  # شعبه مرکزی
    2: "192.168.1.101",  # شعبه 1
    3: "192.168.1.102",  # شعبه 2
}


def get_bridge_service_url(branch_id):
    """دریافت آدرس سرویس واسط بر اساس شعبه"""
    bridge_ip = BRIDGE_SERVICE_MAPPING.get(branch_id)
    if not bridge_ip:
        bridge_ip = list(BRIDGE_SERVICE_MAPPING.values())[0] if BRIDGE_SERVICE_MAPPING else '192.168.1.100'
        print(f"⚠️ شعبه {branch_id} در مپینگ نبود، از {bridge_ip} استفاده شد")

    return f"http://{bridge_ip}:5000/pos/payment"


def send_via_bridge_service(branch_id, pos_ip, amount):
    """ارسال از طریق سرویس واسط"""
    try:
        bridge_service_url = get_bridge_service_url(branch_id)

        payload = {
            'ip': pos_ip,
            'port': 1362,
            'amount': amount
        }

        print(f"🌐 ارسال به سرویس واسط شعبه {branch_id}")
        print(f"📍 آدرس: {bridge_service_url}")

        response = requests.post(bridge_service_url, json=payload, timeout=30)
        result = response.json()

        print(f"✅ پاسخ: {result.get('status')}")
        return result

    except requests.exceptions.ConnectionError:
        bridge_ip = BRIDGE_SERVICE_MAPPING.get(branch_id, 'نامشخص')
        error_msg = f"❌ امکان اتصال به سرویس واسط شعبه {branch_id} (IP: {bridge_ip}) وجود ندارد"
        return {'status': 'error', 'message': error_msg}
    except Exception as e:
        error_msg = f"❌ خطا در ارتباط با سرویس واسط: {str(e)}"
        return {'status': 'error', 'message': error_msg}
@login_required
@csrf_exempt
def add_item_to_invoice(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            ignore_stock = data.get('ignore_stock', False)

            if quantity <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'تعداد باید بیشتر از صفر باشد'
                })

            # بررسی وجود شعبه
            branch_id = request.session.get('branch_id')
            if not branch_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'لطفا ابتدا شعبه را انتخاب کنید'
                })

            product = get_object_or_404(InventoryCount, id=product_id, branch_id=branch_id)

            # بررسی موجودی (مگر اینکه ignore_stock=true باشد)
            if not ignore_stock and product.quantity < quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': f'موجودی کالای {product.product_name} کافی نیست. موجودی فعلی: {product.quantity}',
                    'available_quantity': product.quantity,
                    'product_name': product.product_name
                })

            items = request.session.get('invoice_items', [])
            item_exists = False

            # بررسی وجود آیتم در فاکتور
            for item in items:
                if item['product_id'] == product_id:
                    new_quantity = item['quantity'] + quantity
                    item['quantity'] = new_quantity
                    item['total'] = product.selling_price * new_quantity
                    item_exists = True
                    break

            # اگر آیتم جدید است
            if not item_exists:
                items.append({
                    'product_id': product_id,
                    'product_name': product.product_name,
                    'barcode': product.barcode_data or '',
                    'price': product.selling_price,
                    'quantity': quantity,
                    'total': product.selling_price * quantity,
                    'discount': 0,
                    'available_quantity': product.quantity
                })

            request.session['invoice_items'] = items
            request.session.modified = True

            # محاسبه مبالغ نهایی
            total_without_discount = sum(item['total'] for item in items)
            items_discount = sum(item.get('discount', 0) for item in items)
            invoice_discount = request.session.get('discount', 0)
            total_discount = items_discount + invoice_discount
            total_amount = max(0, total_without_discount - total_discount)

            return JsonResponse({
                'status': 'success',
                'items': items,
                'total_without_discount': total_without_discount,
                'items_discount': items_discount,
                'invoice_discount': invoice_discount,
                'total_discount': total_discount,
                'total_amount': total_amount,
                'message': 'کالا با موفقیت به فاکتور اضافه شد'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا: {str(e)}'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'درخواست نامعتبر'
    })

@login_required
def create_invoice(request):
    if 'branch_id' not in request.session:
        if request.method == 'POST':
            form = BranchSelectionForm(request.POST)
            if form.is_valid():
                request.session['branch_id'] = form.cleaned_data['branch'].id
                request.session['branch_name'] = form.cleaned_data['branch'].name
                request.session['invoice_items'] = []
                return redirect('invoice_app:create_invoice')
        else:
            form = BranchSelectionForm()
        return render(request, 'invoice_create.html', {'form': form, 'branch_selected': False})

    branch_id = request.session.get('branch_id')
    branch = get_object_or_404(Branch, id=branch_id)
    pos_devices = POSDevice.objects.filter(is_active=True)
    default_pos = pos_devices.filter(is_default=True).first()

    return render(request, 'invoice_create.html', {
        'branch_selected': True,
        'branch': branch,
        'pos_devices': pos_devices,
        'default_pos': default_pos,
        'items': request.session.get('invoice_items', []),
        'customer_name': request.session.get('customer_name', ''),
        'customer_phone': request.session.get('customer_phone', ''),
    })

@login_required
@csrf_exempt
def search_product(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            branch_id = request.session.get('branch_id')

            if not branch_id:
                return JsonResponse({'error': 'لطفا ابتدا شعبه را انتخاب کنید'}, status=400)

            if len(query) < 2:
                return JsonResponse({'results': []})

            products = InventoryCount.objects.filter(
                branch_id=branch_id
            ).filter(
                models.Q(product_name__icontains=query) |
                models.Q(barcode_data__icontains=query)
            )[:10]

            results = []
            for product in products:
                results.append({
                    'id': product.id,
                    'name': product.product_name,
                    'barcode': product.barcode_data or '',
                    'quantity': product.quantity,
                    'price': product.selling_price,
                    'low_stock': product.quantity <= 0
                })

            return JsonResponse({'results': results})

        except Exception as e:
            return JsonResponse({'error': f'خطا در جستجو: {str(e)}'}, status=500)

    return JsonResponse({'error': 'درخواست نامعتبر'}, status=400)

@login_required
@csrf_exempt
def remove_item_from_invoice(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')

            items = request.session.get('invoice_items', [])
            items = [item for item in items if item['product_id'] != product_id]

            request.session['invoice_items'] = items
            request.session.modified = True

            total_amount = sum(item['total'] - item.get('discount', 0) for item in items)

            return JsonResponse({
                'status': 'success',
                'items': items,
                'total_amount': total_amount
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})

    return JsonResponse({'status': 'error'})

@login_required
@csrf_exempt
def update_item_quantity(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            new_quantity = int(data.get('quantity', 1))

            if new_quantity <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'تعداد باید بیشتر از صفر باشد'
                })

            product = get_object_or_404(InventoryCount, id=product_id)

            if product.quantity < new_quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': f'موجودی کافی نیست. موجودی فعلی: {product.quantity}'
                })

            items = request.session.get('invoice_items', [])
            item_found = False

            for item in items:
                if item['product_id'] == product_id:
                    item['quantity'] = new_quantity
                    item['total'] = product.selling_price * new_quantity
                    item_found = True
                    break

            if not item_found:
                return JsonResponse({
                    'status': 'error',
                    'message': 'کالا در فاکتور یافت نشد'
                })

            request.session['invoice_items'] = items
            request.session.modified = True

            total_amount = sum(item['total'] - item.get('discount', 0) for item in items)

            return JsonResponse({
                'status': 'success',
                'items': items,
                'total_amount': total_amount,
                'message': 'تعداد کالا با موفقیت به روز شد'
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})

@login_required
@csrf_exempt
def update_item_discount(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            discount = int(data.get('discount', 0))

            if discount < 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'تخفیف نمی‌تواند منفی باشد'
                })

            items = request.session.get('invoice_items', [])
            item_found = False

            for item in items:
                if item['product_id'] == product_id:
                    if discount > item['total']:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'تخفیف نمی‌تواند از قیمت کل بیشتر باشد'
                        })
                    item['discount'] = discount
                    item_found = True
                    break

            if not item_found:
                return JsonResponse({
                    'status': 'error',
                    'message': 'کالا در فاکتور یافت نشد'
                })

            request.session['invoice_items'] = items
            request.session.modified = True

            total_amount = sum(item['total'] - item.get('discount', 0) for item in items)

            return JsonResponse({
                'status': 'success',
                'items': items,
                'total_amount': total_amount,
                'message': 'تخفیف کالا با موفقیت به روز شد'
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})

@login_required
@csrf_exempt
def save_customer_info(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request.session['customer_name'] = data.get('customer_name', '').strip()
            request.session['customer_phone'] = data.get('customer_phone', '').strip()
            request.session.modified = True
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})
    return JsonResponse({'status': 'error'})

@login_required
@csrf_exempt
def save_payment_method(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_method = data.get('payment_method', 'pos')

            if payment_method not in ['cash', 'pos', 'check', 'credit']:
                return JsonResponse({'status': 'error', 'message': 'روش پرداخت نامعتبر'})

            request.session['payment_method'] = payment_method

            if payment_method == 'pos':
                default_pos = POSDevice.objects.filter(is_default=True, is_active=True).first()
                if default_pos:
                    request.session['pos_device_id'] = default_pos.id
            else:
                if 'pos_device_id' in request.session:
                    del request.session['pos_device_id']
                if 'check_payment_data' in request.session:
                    del request.session['check_payment_data']
                if 'credit_payment_data' in request.session:
                    del request.session['credit_payment_data']

            request.session.modified = True
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})
    return JsonResponse({'status': 'error'})

@login_required
@csrf_exempt
def save_pos_device(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')

            if not device_id:
                return JsonResponse({'status': 'error', 'message': 'دستگاه انتخاب نشده'})

            device = get_object_or_404(POSDevice, id=device_id, is_active=True)
            request.session['pos_device_id'] = device.id
            request.session.modified = True

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})
    return JsonResponse({'status': 'error'})

@login_required
@csrf_exempt
def save_check_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("📋 اطلاعات دریافتی چک:", data)  # لاگ برای دیباگ

            required_fields = ['owner_name', 'owner_family', 'national_id', 'phone',
                               'check_number', 'amount', 'check_date', 'remaining_amount',
                               'remaining_payment_method']

            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'status': 'error', 'message': f'فیلد {field} الزامی است'})

            # ذخیره اطلاعات چک در session
            check_data = {
                'owner_name': data.get('owner_name', '').strip(),
                'owner_family': data.get('owner_family', '').strip(),
                'national_id': data.get('national_id', '').strip(),
                'address': data.get('address', '').strip(),
                'phone': data.get('phone', '').strip(),
                'check_number': data.get('check_number', '').strip(),
                'amount': int(data.get('amount', 0)),
                'remaining_amount': int(data.get('remaining_amount', 0)),
                'remaining_payment_method': data.get('remaining_payment_method', 'cash'),
                'remaining_pos_device_id': data.get('remaining_pos_device_id'),
                'check_date': data.get('check_date', '')
            }

            request.session['check_payment_data'] = check_data
            request.session.modified = True

            print("✅ اطلاعات چک در session ذخیره شد:", check_data)

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"❌ خطا در ذخیره اطلاعات چک: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})
    return JsonResponse({'status': 'error'})


@login_required
@csrf_exempt
def save_discount(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            discount = int(data.get('discount', 0))

            if discount < 0:
                return JsonResponse({'status': 'error', 'message': 'تخفیف نمی‌تواند منفی باشد'})

            request.session['discount'] = discount
            request.session.modified = True

            items = request.session.get('invoice_items', [])
            total_amount = sum(item['total'] - item.get('discount', 0) for item in items) - discount
            total_amount = max(0, total_amount)

            return JsonResponse({
                'status': 'success',
                'total_amount': total_amount
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})
    return JsonResponse({'status': 'error'})

@login_required
@csrf_exempt
def manage_pos_devices(request):
    """
    Handle all POS device operations (add, delete, set_default)
    """
    if request.method == 'POST':
        try:
            action = request.POST.get('action')

            if action == 'add':
                name = request.POST.get('name', '').strip()
                account_holder = request.POST.get('account_holder', '').strip()
                card_number = request.POST.get('card_number', '').strip()
                account_number = request.POST.get('account_number', '').strip()
                bank_name = request.POST.get('bank_name', '').strip()

                errors = {}
                if not name:
                    errors['name'] = ['نام دستگاه الزامی است']
                if not account_holder:
                    errors['account_holder'] = ['نام صاحب حساب الزامی است']
                if not card_number:
                    errors['card_number'] = ['شماره کارت الزامی است']
                elif len(card_number) != 16 or not card_number.isdigit():
                    errors['card_number'] = ['شماره کارت باید 16 رقم باشد']
                if not account_number:
                    errors['account_number'] = ['شماره حساب الزامی است']
                if not bank_name:
                    errors['bank_name'] = ['نام بانک الزامی است']

                if errors:
                    return JsonResponse({
                        'status': 'error',
                        'errors': errors
                    })

                pos_device = POSDevice.objects.create(
                    name=name,
                    account_holder=account_holder,
                    card_number=card_number,
                    account_number=account_number,
                    bank_name=bank_name
                )

                if POSDevice.objects.filter(is_active=True).count() == 1:
                    pos_device.is_default = True
                    pos_device.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'دستگاه با موفقیت اضافه شد',
                    'device_id': pos_device.id,
                    'device_name': f"{pos_device.name} - {pos_device.bank_name}"
                })

            elif action == 'delete':
                device_id = request.POST.get('device_id')
                device = get_object_or_404(POSDevice, id=device_id)
                device.delete()
                return JsonResponse({'status': 'success', 'message': 'دستگاه حذف شد'})

            elif action == 'set_default':
                device_id = request.POST.get('device_id')
                POSDevice.objects.filter(is_default=True).update(is_default=False)
                device = get_object_or_404(POSDevice, id=device_id)
                device.is_default = True
                device.save()
                return JsonResponse({'status': 'success', 'message': 'دستگاه پیش فرض تغییر کرد'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})

@login_required
def invoice_success(request, invoice_id):
    """
    نمایش صفحه موفقیت آمیز بودن ثبت فاکتور
    """
    try:
        invoice = get_object_or_404(Invoicefrosh, id=invoice_id)

        # لاگ کردن برای پیگیری
        print(f"📄 نمایش صفحه موفقیت برای فاکتور {invoice_id}")

        # استفاده از redirect به جای render اگر مشکل template باقی ماند
        return render(request, 'invoice_success.html', {
            'invoice': invoice,
            'success_message': 'فاکتور با موفقیت ثبت شد و صفحه برای فاکتور جدید آماده است.'
        })

    except Exception as e:
        print(f"❌ خطا در نمایش صفحه موفقیت: {str(e)}")
        # fallback به یک صفحه ساده
        return render(request, 'simple_success.html', {
            'invoice_id': invoice_id,
            'message': 'فاکتور با موفقیت ثبت شد'
        })

@login_required
def invoice_print(request, invoice_id):
    invoice = get_object_or_404(Invoicefrosh, id=invoice_id)

    payment_details = None
    payment_type = None

    if invoice.payment_method == 'check' and hasattr(invoice, 'check_payment'):
        payment_details = invoice.check_payment
        payment_type = 'check'
    elif invoice.payment_method == 'credit' and hasattr(invoice, 'credit_payment'):
        payment_details = invoice.credit_payment
        payment_type = 'credit'
    elif invoice.payment_method == 'pos' and invoice.pos_device:
        payment_details = invoice.pos_device
        payment_type = 'pos'

    from jdatetime import datetime as jdatetime
    jalali_date = jdatetime.fromgregorian(datetime=invoice.created_at).strftime('%Y/%m/%d')
    jalali_time = jdatetime.fromgregorian(datetime=invoice.created_at).strftime('%H:%M')

    return render(request, 'invoice_print.html', {
        'invoice': invoice,
        'payment_details': payment_details,
        'payment_type': payment_type,
        'jalali_date': jalali_date,
        'jalali_time': jalali_time,
        'print_date': jdatetime.now().strftime('%Y/%m/%d %H:%M')
    })

@login_required
def get_invoice_summary(request):
    """
    دریافت خلاصه فاکتور از session
    """
    if request.method == 'GET':
        try:
            items = request.session.get('invoice_items', [])
            discount = request.session.get('discount', 0)

            # اگر session پاک شده باشد
            if not items and 'invoice_items' not in request.session:
                return JsonResponse({
                    'session_cleared': True,
                    'message': 'session فاکتور خالی است',
                    'success': True
                })

            # محاسبه دقیق مبالغ
            total_without_discount = sum(item['total'] for item in items)
            items_discount = sum(item.get('discount', 0) for item in items)
            total_discount = items_discount + discount
            total_amount = max(0, total_without_discount - total_discount)

            return JsonResponse({
                'session_cleared': False,
                'total_items': len(items),
                'total_without_discount': total_without_discount,
                'items_discount': items_discount,
                'invoice_discount': discount,
                'total_discount': total_discount,
                'total_amount': total_amount,
                'success': True
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'success': False
            })

    return JsonResponse({
        'error': 'درخواست نامعتبر',
        'success': False
    })

# فقط این یک تابع cancel_invoice باید باقی بماند - تابع تکراری را حذف کنید
@login_required
def cancel_invoice(request):
    """
    ویوی لغو فاکتور و پاکسازی کامل session
    سپس ریدایرکت به صفحه ایجاد فاکتور برای نمایش فرم انتخاب شعبه
    """
    print("🔴 درخواست لغو فاکتور دریافت شد")

    session_keys_to_remove = [
        'invoice_items', 'customer_name', 'customer_phone',
        'payment_method', 'discount', 'pos_device_id',
        'check_payment_data', 'credit_payment_data', 'branch_id', 'branch_name'
    ]

    removed_keys = []
    for key in session_keys_to_remove:
        if key in request.session:
            del request.session[key]
            removed_keys.append(key)

    request.session.modified = True

    print(f"✅ session پاکسازی شد. کلیدهای حذف شده: {removed_keys}")

    # ریدایرکت به صفحه ایجاد فاکتور که فرم انتخاب شعبه را نشان می‌دهد
    return redirect('invoice_app:create_invoice')


@login_required
@csrf_exempt
def confirm_check_payment(request):
    """
    تأیید نهایی پرداخت چک و ثبت فاکتور
    """
    if request.method == 'POST':
        try:
            # بررسی وجود اطلاعات چک در session
            check_data = request.session.get('check_payment_data')
            if not check_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'اطلاعات چک یافت نشد. لطفا مجدداً اطلاعات چک را وارد کنید.'
                })

            # فراخوانی ویوی نهایی کردن فاکتور
            return finalize_invoice(request)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در تأیید پرداخت چک: {str(e)}'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'درخواست نامعتبر'
    })


@login_required
@csrf_exempt
def save_credit_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("📋 اطلاعات دریافتی نسیه:", data)

            # 🔴 اصلاح: استفاده از credit_amount از داده‌های فرم
            credit_amount = int(data.get('credit_amount', 0))

            # ذخیره اطلاعات کامل در session
            credit_data = {
                'customer_name': data.get('customer_name', '').strip(),
                'customer_family': data.get('customer_family', '').strip(),
                'national_id': data.get('national_id', '').strip(),
                'address': data.get('address', '').strip(),
                'phone': data.get('phone', '').strip(),
                'due_date': data.get('due_date', ''),
                # 🔴 استفاده از credit_amount از فرم، نه total_amount
                'credit_amount': credit_amount,
                'remaining_amount': data.get('remaining_amount', 0),
                'remaining_payment_method': data.get('remaining_payment_method', 'cash'),
                'remaining_pos_device_id': data.get('remaining_pos_device_id')
            }

            request.session['credit_payment_data'] = credit_data
            request.session.modified = True

            print("✅ اطلاعات نسیه در session ذخیره شد:", credit_data)
            return JsonResponse({'status': 'success'})

        except Exception as e:
            print(f"❌ خطا در ذخیره اطلاعات نسیه: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})
    return JsonResponse({'status': 'error'})


# invoice_app/views.py (بخش اصلاح شده)



# ==================== توابع ارتباط با پوز ====================


def normalize_ip(ip):
    """نرمال کردن آدرس IP"""
    parts = ip.split('.')
    normalized_parts = [str(int(part)) for part in parts]
    return '.'.join(normalized_parts)


def build_sale_request(amount):
    """ساخت پیام با فرمت 12 رقمی استاندارد برای دستگاه پوز - amount باید ریال باشد"""
    print(f"🔨 شروع ساخت پیام برای دستگاه پوز")
    print(f"💰 مبلغ ورودی: {amount} ریال")

    # اطمینان از عدد بودن مبلغ
    try:
        amount_int = int(amount)
    except (ValueError, TypeError):
        print(f"❌ مبلغ نامعتبر: {amount}")
        raise ValueError("مبلغ باید عدد باشد")

    # تبدیل به 12 رقم با صفرهای ابتدایی
    amount_12_digit = str(amount_int).zfill(12)
    print(f"💰 مبلغ 12 رقمی: {amount_12_digit}")

    # بررسی طول مبلغ
    if len(str(amount_int)) > 12:
        print(f"❌ مبلغ بیش از حد بزرگ است: {amount_int}")
        raise ValueError("مبلغ نمی‌تواند بیش از 12 رقم باشد")

    # استفاده از فرمت 12 رقمی استاندارد
    message = f"0047RQ034PR006000000AM012{amount_12_digit}CU003364PD0011"

    print(f"📦 پیام نهایی ساخته شد:")
    print(f"   طول: {len(message)}")
    print(f"   محتوا: {message}")
    print(f"   HEX: {message.encode('ascii').hex()}")

    return message



# ==================== ویوهای اصلی فاکتور ====================

@login_required
@csrf_exempt
def finalize_invoice(request):
    """ویوی نهایی کردن فاکتور"""
    if request.method == 'POST':
        try:
            branch_id = request.session.get('branch_id')
            items = request.session.get('invoice_items', [])
            payment_method = request.session.get('payment_method', 'pos')

            if not branch_id:
                return JsonResponse({'status': 'error', 'message': 'شعبه انتخاب نشده'})

            if not items:
                return JsonResponse({'status': 'error', 'message': 'فاکتور خالی است'})

            # محاسبه مبلغ
            total_amount = sum(item['total'] - item.get('discount', 0) for item in items)
            total_amount -= request.session.get('discount', 0)
            total_amount = max(0, total_amount)

            print(f"💰 مبلغ فاکتور: {total_amount} تومان - شعبه: {branch_id}")

            # اگر پرداخت POS است
            if payment_method == 'pos':
                pos_device_id = request.session.get('pos_device_id')
                if not pos_device_id:
                    return JsonResponse({'status': 'error', 'message': 'دستگاه پوز انتخاب نشده'})

                branch = get_object_or_404(Branch, id=branch_id)
                pos_device = get_object_or_404(POSDevice, id=pos_device_id, is_active=True)

                branch_modem_ip = branch.modem_ip
                if not branch_modem_ip:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'IP مودم برای شعبه {branch.name} تنظیم نشده'
                    })

                # تبدیل به ریال و ارسال
                amount_rial = total_amount * 10

                print(f"🎯 ارسال از طریق سرویس واسط")
                pos_result = send_via_bridge_service(branch_id, branch_modem_ip, amount_rial)

                if pos_result['status'] != 'success':
                    return JsonResponse({
                        'status': 'error',
                        'message': f'خطا در پرداخت پوز: {pos_result["message"]}'
                    })

                print("✅ پرداخت پوز موفق بود")

            # ثبت فاکتور
            invoice = Invoicefrosh.objects.create(
                branch_id=branch_id,
                total_amount=total_amount,
                payment_method=payment_method,
                customer_name=request.session.get('customer_name', ''),
                customer_phone=request.session.get('customer_phone', ''),
                created_by=request.user
            )

            # ثبت آیتم‌ها
            for item_data in items:
                product = InventoryCount.objects.get(id=item_data['product_id'])
                InvoiceItemfrosh.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=item_data['quantity'],
                    price=item_data['price'],
                    discount=item_data.get('discount', 0)
                )
                product.quantity -= item_data['quantity']
                product.save()

            # پاکسازی session
            session_keys = ['invoice_items', 'customer_name', 'customer_phone',
                            'payment_method', 'discount', 'pos_device_id']
            for key in session_keys:
                if key in request.session:
                    del request.session[key]

            return JsonResponse({
                'status': 'success',
                'message': 'فاکتور با موفقیت ثبت شد',
                'invoice_id': invoice.id
            })

        except Exception as e:
            print(f"❌ خطا در ثبت فاکتور: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در ثبت فاکتور: {str(e)}'
            })

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})
# --------------------------------------------------------------------------
@login_required
@csrf_exempt
def process_pos_payment(request):
    """پردازش پرداخت از طریق پوز - بهبود یافته با مدیریت وضعیت‌ها"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount_toman = data.get('amount')  # مبلغ به تومان
            pos_device_id = data.get('pos_device_id')

            print(f"🔄 شروع پردازش پرداخت POS")
            print(f"📊 داده‌های دریافتی: amount_toman={amount_toman}, device_id={pos_device_id}")

            if not amount_toman:
                return JsonResponse({
                    'status': 'error',
                    'message': 'مبلغ الزامی است'
                })

            if not pos_device_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'دستگاه پوز الزامی است'
                })

            # 🔴 دریافت شعبه از session
            branch_id = request.session.get('branch_id')
            if not branch_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'شعبه انتخاب نشده است'
                })

            try:
                branch = Branch.objects.get(id=branch_id)
                print(f"🏢 شعبه: {branch.name}")

                # 🔴 دریافت IP مودم از شعبه
                branch_modem_ip = branch.modem_ip
                if not branch_modem_ip:
                    print(f"❌ IP مودم برای شعبه {branch.name} تنظیم نشده است")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'IP مودم برای شعبه {branch.name} تنظیم نشده است. لطفا با مدیر سیستم تماس بگیرید.'
                    })

                print(f"📡 IP مودم شعبه: {branch_modem_ip}")

            except Branch.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'شعبه یافت نشد'
                })

            # تبدیل تومان به ریال (ضرب در 10)
            amount_rial = int(amount_toman) * 10
            print(f"💸 تبدیل مبلغ: {amount_toman} تومان → {amount_rial} ریال")

            # دریافت اطلاعات دستگاه پوز
            try:
                pos_device = POSDevice.objects.get(id=pos_device_id, is_active=True)
                print(f"📟 دستگاه پوز یافت شد: {pos_device.name}")
            except POSDevice.DoesNotExist:
                print(f"❌ دستگاه پوز با ID {pos_device_id} یافت نشد")
                return JsonResponse({
                    'status': 'error',
                    'message': 'دستگاه پوز یافت نشد'
                })

            # دریافت پورت از دستگاه پوز
            pos_port = getattr(pos_device, 'port', 1362)

            print(f"📍 اطلاعات اتصال:")
            print(f"   شعبه: {branch.name}")
            print(f"   دستگاه: {pos_device.name}")
            print(f"   IP مودم: {branch_modem_ip}")
            print(f"   پورت: {pos_port}")

            # 🔴 ارسال مبلغ ریال به دستگاه پوز با استفاده از IP مودم شعبه
            print(f"🚀 شروع ارسال به دستگاه پوز...")
            pos_result = send_to_pos_with_status(branch_modem_ip, pos_port, amount_rial)

            # بررسی وضعیت تراکنش
            if pos_result['status'] == 'success':
                transaction_status = pos_result.get('transaction_status', {})

                if transaction_status.get('status_type') == 'success':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'پرداخت با موفقیت انجام شد',
                        'transaction_status': transaction_status,
                        'amount_toman': amount_toman,
                        'amount_rial': amount_rial,
                        'branch_info': {
                            'name': branch.name,
                            'modem_ip': branch_modem_ip
                        },
                        'device_info': {
                            'name': pos_device.name,
                            'port': pos_port
                        },
                        'pos_response': pos_result
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': transaction_status.get('message', 'خطا در پرداخت'),
                        'transaction_status': transaction_status
                    })
            else:
                print(f"❌ خطا در پرداخت POS: {pos_result['message']}")
                return JsonResponse({
                    'status': 'error',
                    'message': pos_result['message'],
                    'transaction_status': {
                        'status_type': 'connection_error',
                        'message': pos_result['message']
                    }
                })

        except json.JSONDecodeError as json_error:
            print(f"❌ خطای JSON: {json_error}")
            return JsonResponse({
                'status': 'error',
                'message': 'داده‌های ارسالی معتبر نیستند'
            })
        except Exception as e:
            print(f"❌ خطای غیرمنتظره در پردازش پرداخت: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در پردازش پرداخت: {str(e)}'
            })

def receive_full_response(sock, timeout=30):  # افزایش به 30 ثانیه
    """دریافت کامل پاسخ از سوکت با مدیریت timeout"""
    print(f"⏳ شروع دریافت پاسخ از دستگاه پوز - timeout: {timeout} ثانیه")

    sock.settimeout(timeout)
    response = b""
    start_time = time.time()

    try:
        while True:
            try:
                # زمان باقیمانده را محاسبه کن
                elapsed_time = time.time() - start_time
                remaining_time = timeout - elapsed_time

                if remaining_time <= 0:
                    print("⏰ زمان دریافت پاسخ به پایان رسید")
                    break

                # از timeout اصلی استفاده کن، نه timeout کوتاه
                sock.settimeout(remaining_time)
                chunk = sock.recv(1024)

                if chunk:
                    response += chunk
                    print(f"📥 دریافت بسته داده: {len(chunk)} بایت")
                    print(f"📋 محتوای بسته: {chunk}")
                    print(f"🔢 HEX بسته: {chunk.hex()}")

                    # اگر پاسخ کامل دریافت شده، خارج شو
                    if len(response) >= 4:
                        try:
                            length_part = response[:4].decode('ascii')
                            expected_length = int(length_part)
                            if len(response) >= expected_length:
                                print(f"✅ پاسخ کامل دریافت شد. طول مورد انتظار: {expected_length}")
                                break
                        except (ValueError, UnicodeDecodeError):
                            # اگر نتوانستیم طول را parse کنیم، ادامه می‌دهیم
                            pass

                else:
                    print("📭 اتصال بسته شد")
                    break

            except socket.timeout:
                print("⏰ timeout در دریافت داده - بررسی می‌کنیم آیا پاسخ کافی دریافت شده")
                # فقط اگر واقعاً timeout اصلی رسیده باشد خارج شو
                elapsed_time = time.time() - start_time
                if elapsed_time >= timeout:
                    print("⏰ timeout اصلی رسید")
                    break
                else:
                    # اگر timeout اصلی نرسیده، ادامه بده
                    print(f"⏱️ هنوز {timeout - elapsed_time:.1f} ثانیه زمان باقی است")
                    continue

    except Exception as e:
        print(f"❌ خطای کلی در دریافت پاسخ: {e}")

    end_time = time.time()
    duration = end_time - start_time
    print(f"⏱️ مدت زمان دریافت پاسخ: {duration:.2f} ثانیه")
    print(f"📦 اندازه پاسخ نهایی: {len(response)} بایت")

    return response


def send_to_pos_with_status(ip, port, amount):
    """ارسال مبلغ به دستگاه پوز با مدیریت کامل وضعیت‌ها"""
    try:
        print(f"💰 ارسال تراکنش برای مبلغ: {amount} ریال به {ip}:{port}")

        if not ip:
            return {
                'status': 'error',
                'message': 'آدرس IP نمی‌تواند خالی باشد',
                'transaction_status': {
                    'status_type': 'connection_error',
                    'message': 'آدرس IP معتبر نیست'
                }
            }

        ip = normalize_ip(ip)
        if not is_valid_ip(ip):
            return {
                'status': 'error',
                'message': 'آدرس IP معتبر نیست',
                'transaction_status': {
                    'status_type': 'connection_error',
                    'message': 'آدرس IP معتبر نیست'
                }
            }

        # ساخت پیام با فرمت 12 رقمی
        message = build_sale_request(amount)

        print(f"📤 ارسال پیام به دستگاه...")
        print(f"📦 پیام ارسالی: {message}")
        print(f"🔢 پیام HEX: {message.encode('ascii').hex()}")

        # ارسال به دستگاه
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # timeout اتصال
        print(f"🔌 در حال اتصال به {ip}:{port}...")

        try:
            sock.connect((ip, port))
        except socket.timeout:
            return {
                'status': 'error',
                'message': 'اتصال به دستگاه پوز timeout خورد',
                'transaction_status': {
                    'status_type': 'connection_error',
                    'message': 'دستگاه پوز در دسترس نیست'
                }
            }

        print("✅ اتصال برقرار شد")

        bytes_sent = sock.send(message.encode('ascii'))
        print(f"✅ {bytes_sent} بایت ارسال شد")

        # زمان برای نمایش مبلغ روی دستگاه
        print("⏳ منتظر نمایش مبلغ روی دستگاه...")
        time.sleep(3)  # 3 ثانیه صبر کن

        # دریافت پاسخ از دستگاه با timeout 30 ثانیه
        print("⏳ در حال دریافت پاسخ از دستگاه پوز...")
        response = receive_full_response(sock, timeout=30)  # 30 ثانیه کامل

        sock.close()
        print("🔒 اتصال بسته شد")

        # تحلیل وضعیت تراکنش
        response_text = response.decode('ascii', errors='ignore') if response else ""
        status_info = get_transaction_status(len(response), response_text)

        print(f"📋 نتیجه تراکنش: {status_info}")

        return {
            'status': 'success',
            'message': f'تراکنش {amount} ریال ارسال شد',
            'transaction_status': status_info,
            'debug': {
                'message_sent': message,
                'response': response_text,
                'response_length': len(response),
                'bytes_sent': bytes_sent,
                'ip_port': f'{ip}:{port}',
                'total_wait_time': '30 ثانیه'
            }
        }

    except socket.timeout as timeout_error:
        print(f"⏰ خطای timeout در اتصال: {timeout_error}")
        return {
            'status': 'error',
            'message': f'اتصال timeout - دستگاه پوز پاسخ نداد: {str(timeout_error)}',
            'transaction_status': {
                'status_type': 'timeout',
                'message': 'زمان پرداخت به پایان رسید. لطفاً مجدداً تلاش کنید.'
            }
        }
    except ConnectionRefusedError as conn_error:
        print(f"🔌 خطای اتصال: {conn_error}")
        return {
            'status': 'error',
            'message': f'اتصال رد شد - پورت باز نیست یا دستگاه خاموش است: {str(conn_error)}',
            'transaction_status': {
                'status_type': 'connection_error',
                'message': 'دستگاه پوز پاسخ نمی‌دهد. از روشن بودن دستگاه اطمینان حاصل کنید.'
            }
        }
    except Exception as e:
        print(f"❌ خطا در ارسال به پوز: {e}")
        return {
            'status': 'error',
            'message': f'خطا در ارسال تراکنش: {str(e)}',
            'transaction_status': {
                'status_type': 'error',
                'message': f'خطا در ارسال تراکنش: {str(e)}'
            }
        }

def get_transaction_status(response_length, response_text):
    """تعیین وضعیت تراکنش بر اساس طول پیام پاسخ"""
    print(f"🔍 تحلیل وضعیت تراکنش - طول پاسخ: {response_length}")

    # اگر پاسخی دریافت نشده باشد
    if response_length == 0:
        return {
            'status_type': 'timeout',
            'message': '⚠️ دستگاه پوز پاسخی ارسال نکرد. ممکن است تراکنش کنسل شده باشد یا ارتباط قطع شده است.'
        }

    # استخراج طول پیام از 4 کاراکتر اول (در صورت موجود بودن)
    length_part = ""
    if response_text and len(response_text) >= 4:
        length_part = response_text[:4]
        print(f"📏 طول پیام از 4 کاراکتر اول: {length_part}")

    # تشخیص وضعیت بر اساس طول پیام
    status_info = {
        'length': response_length,
        'length_part': length_part,
        'message': '',
        'status_type': 'unknown'
    }

    # تشخیص بر اساس طول پیام
    if response_length == 130:  # 0130 به صورت دهدهی
        status_info['message'] = "✅ پرداخت موفق بود - تراکنش با موفقیت انجام شد"
        status_info['status_type'] = 'success'
    elif response_length == 29:  # 0029 به صورت دهدهی
        status_info['message'] = "❌ رمز کارت اشتباه بود - لطفا مجدداً تلاش کنید"
        status_info['status_type'] = 'error'
    elif response_length == 18:  # 0018 به صورت دهدهی
        status_info['message'] = "⚠️ پرداخت کنسل شد - کاربر عملیات را لغو کرد"
        status_info['status_type'] = 'cancelled'
    elif response_length == 24:  # 0018 به صورت دهدهی؟ بررسی کنید
        status_info['message'] = "⚠️ پرداخت کنسل شد - کاربر عملیات را لغو کرد"
        status_info['status_type'] = 'cancelled'
    else:
        # اگر طول شناخته شده نبود، بر اساس length_part چک می‌کنیم
        if length_part == "0130":
            status_info['message'] = "✅ پرداخت موفق بود - تراکنش با موفقیت انجام شد"
            status_info['status_type'] = 'success'
        elif length_part == "0029":
            status_info['message'] = "❌ رمز کارت اشتباه بود - لطفا مجدداً تلاش کنید"
            status_info['status_type'] = 'error'
        elif length_part == "0018":
            status_info['message'] = "⚠️ پرداخت کنسل شد - کاربر عملیات را لغو کرد"
            status_info['status_type'] = 'cancelled'
        else:
            status_info['message'] = f"🔍 وضعیت نامشخص - طول پاسخ: {response_length}, کد: {length_part}"
            status_info['status_type'] = 'unknown'

    print(f"📋 نتیجه تحلیل: {status_info['message']}")
    return status_info

# ------------------------------------------------------------------------------------------
import socket
import time
import re


def send_to_pos_from_server(ip, port, amount):
    """ارسال مستقیم از سرور به دستگاه پوز - نسخه ساده و مطمئن"""
    try:
        print(f"🚀 ارسال از سرور به پوز: {amount} ریال به {ip}:{port}")

        # اعتبارسنجی IP
        if not ip or not is_valid_ip(ip):
            return {
                'status': 'error',
                'message': 'آدرس IP معتبر نیست'
            }

        # ساخت پیام ساده
        amount_str = str(amount).zfill(12)
        message = f"0047RQ034PR006000000AM012{amount_str}CU003364PD0011"

        print(f"📦 پیام ارسالی: {message}")

        # ارسال به دستگاه پوز
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)  # کاهش timeout
        sock.connect((ip, port))

        # ارسال پیام
        sock.send(message.encode('ascii'))
        print("✅ پیام ارسال شد")

        # کمی صبر کن
        time.sleep(2)

        # دریافت پاسخ
        response = b""
        try:
            sock.settimeout(10)
            response = sock.recv(1024)
            print(f"📥 پاسخ دریافت شد: {response}")
        except socket.timeout:
            print("⚠️ پاسخی دریافت نشد")
        finally:
            sock.close()

        return {
            'status': 'success',
            'message': 'مبلغ به پوز ارسال شد',
            'response': response.decode('ascii', errors='ignore') if response else "بدون پاسخ"
        }

    except ConnectionRefusedError:
        return {
            'status': 'error',
            'message': 'دستگاه پوز روشن نیست یا پورت باز نیست'
        }
    except socket.timeout:
        return {
            'status': 'error',
            'message': 'اتصال timeout خورد'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'خطا: {str(e)}'
        }


def is_valid_ip(ip):
    """بررسی ساده IP"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except:
        return False


@login_required
def quick_pos_test(request):
    """تست سریع + مدیریت مپینگ پوز بریج"""
    branches = Branch.objects.all()

    # ایجاد لیست از مپینگ‌های فعلی
    current_mapping = []
    for branch in branches:
        current_mapping.append({
            'branch': branch,
            'bridge_ip': BRIDGE_SERVICE_MAPPING.get(branch.id, 'تعیین نشده')
        })

    if request.method == 'POST':
        # به روز کردن مپینگ
        for branch in branches:
            new_ip = request.POST.get(f'branch_{branch.id}', '').strip()
            if new_ip:
                BRIDGE_SERVICE_MAPPING[branch.id] = new_ip
                print(f"✅ مپینگ به روز شد: شعبه {branch.id} -> {new_ip}")

        return redirect('invoice_app:quick_pos_test')

    return render(request, 'bridge_mapping.html', {
        'current_mapping': current_mapping,
        'branches': branches,
    })



# --------------------------------
@login_required
def bridge_mapping_view(request):
    """مدیریت مپینگ شعبه به سرویس واسط"""
    branches = Branch.objects.all()

    current_mapping = []
    for branch in branches:
        current_mapping.append({
            'branch': branch,
            'bridge_ip': BRIDGE_SERVICE_MAPPING.get(branch.id, 'تعیین نشده')
        })

    if request.method == 'POST':
        for branch in branches:
            new_ip = request.POST.get(f'branch_{branch.id}', '').strip()
            if new_ip:
                BRIDGE_SERVICE_MAPPING[branch.id] = new_ip
                print(f"✅ مپینگ به روز شد: شعبه {branch.id} -> {new_ip}")

        return redirect('invoice_app:bridge_mapping')

    return render(request, 'bridge_mapping.html', {
        'current_mapping': current_mapping,
        'branches': branches,
    })


@login_required
@csrf_exempt
def test_bridge_connection(request):
    """تست ارتباط با سرویس واسط"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            branch_id = data.get('branch_id')

            if not branch_id:
                return JsonResponse({'status': 'error', 'message': 'شعبه مشخص نشده'})

            bridge_ip = BRIDGE_SERVICE_MAPPING.get(int(branch_id))
            if not bridge_ip:
                return JsonResponse({'status': 'error', 'message': 'سرویس واسط برای این شعبه تنظیم نشده'})

            health_url = f"http://{bridge_ip}:5000/health"
            response = requests.get(health_url, timeout=10)

            if response.status_code == 200:
                return JsonResponse({
                    'status': 'success',
                    'message': f'سرویس واسط شعبه {branch_id} فعال است',
                    'bridge_ip': bridge_ip
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'سرویس واسط پاسخ نمی‌دهد'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در تست ارتباط: {str(e)}'
            })

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})


@login_required
@csrf_exempt
def quick_pos_test_api(request):
    """API برای تست ارتباط با سرویس واسط"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            branch_id = data.get('branch_id')

            if not branch_id:
                return JsonResponse({'status': 'error', 'message': 'شعبه مشخص نشده'})

            bridge_ip = BRIDGE_SERVICE_MAPPING.get(int(branch_id))
            if not bridge_ip:
                return JsonResponse({'status': 'error', 'message': 'سرویس واسط برای این شعبه تنظیم نشده'})

            # تست سلامت سرویس
            health_url = f"http://{bridge_ip}:5000/health"
            response = requests.get(health_url, timeout=10)

            if response.status_code == 200:
                health_data = response.json()
                return JsonResponse({
                    'status': 'success',
                    'message': f'سرویس واسط شعبه {branch_id} فعال است',
                    'bridge_ip': bridge_ip,
                    'health_data': health_data
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'سرویس واسط پاسخ نمی‌دهد. کد وضعیت: {response.status_code}'
                })

        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'status': 'error',
                'message': f'امکان اتصال به سرویس واسط در {bridge_ip} وجود ندارد'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در تست ارتباط: {str(e)}'
            })

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})