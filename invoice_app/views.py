
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

# invoice_app/views.py (بخش اصلاح شده)

import socket
import json
import re
import time
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


# ==================== توابع ارتباط با پوز ====================

def is_valid_ip(ip):
    """بررسی معتبر بودن آدرس IP"""
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    if not re.match(pattern, ip):
        return False
    parts = ip.split('.')
    for part in parts:
        if not 0 <= int(part) <= 255:
            return False
    return True

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

def send_to_pos(ip, port, amount):
    """ارسال مبلغ به دستگاه پوز - amount باید به ریال باشد"""
    try:
        print(f"💰 ارسال تراکنش برای مبلغ: {amount} ریال به {ip}:{port}")

        if not ip:
            return {'status': 'error', 'message': 'آدرس IP نمی‌تواند خالی باشد'}

        ip = normalize_ip(ip)
        if not is_valid_ip(ip):
            return {'status': 'error', 'message': 'آدرس IP معتبر نیست'}

        # ساخت پیام با فرمت 12 رقمی - amount باید ریال باشد
        message = build_sale_request(amount)

        print(f"📤 ارسال پیام به دستگاه...")
        print(f"📦 پیام ارسالی: {message}")
        print(f"🔢 پیام HEX: {message.encode('ascii').hex()}")

        # ارسال به دستگاه
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        print(f"🔌 در حال اتصال به {ip}:{port}...")
        sock.connect((ip, port))
        print("✅ اتصال برقرار شد")

        bytes_sent = sock.send(message.encode('ascii'))
        print(f"✅ {bytes_sent} بایت ارسال شد")

        # زمان برای نمایش مبلغ روی دستگاه
        print("⏳ منتظر نمایش مبلغ روی دستگاه...")
        time.sleep(3)

        response = b""
        try:
            print("📥 در حال دریافت پاسخ از دستگاه...")
            response = sock.recv(1024)
            if response:
                print(f"📥 پاسخ دریافت شد: {len(response)} بایت")
                print(f"📋 محتوای پاسخ: {response.decode('ascii', errors='ignore')}")
                print(f"🔢 پاسخ HEX: {response.hex()}")
            else:
                print("⚠️ پاسخ خالی از دستگاه")
        except socket.timeout:
            print("⏰ timeout در دریافت پاسخ - دستگاه پاسخی ارسال نکرد")
        except Exception as recv_error:
            print(f"❌ خطا در دریافت پاسخ: {recv_error}")

        sock.close()
        print("🔒 اتصال بسته شد")

        response_text = response.decode('ascii', errors='ignore') if response else "بدون پاسخ"

        return {
            'status': 'success',
            'message': f'تراکنش {amount} ریال ارسال شد',
            'on_pos': 'مبلغ باید روی پوز نمایش داده شود',
            'debug': {
                'message_sent': message,
                'response': response_text,
                'bytes_sent': bytes_sent,
                'ip_port': f'{ip}:{port}',
                'note': 'استفاده از فرمت 12 رقمی استاندارد'
            }
        }

    except socket.timeout as timeout_error:
        print(f"⏰ خطای timeout در اتصال: {timeout_error}")
        return {
            'status': 'error',
            'message': f'اتصال timeout - دستگاه پوز پاسخ نداد: {str(timeout_error)}'
        }
    except ConnectionRefusedError as conn_error:
        print(f"🔌 خطای اتصال: {conn_error}")
        return {
            'status': 'error',
            'message': f'اتصال رد شد - پورت باز نیست یا دستگاه خاموش است: {str(conn_error)}'
        }
    except Exception as e:
        print(f"❌ خطا در ارسال به پوز: {e}")
        return {
            'status': 'error',
            'message': f'خطا در ارسال تراکنش: {str(e)}'
        }
# ==================== ویوهای اصلی فاکتور ====================

@login_required
@csrf_exempt
def process_pos_payment(request):
    """پردازش پرداخت از طریق پوز - amount ورودی تومان است"""
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
            except Branch.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'شعبه یافت نشد'
                })

            # 🔴 دریافت IP مودم از شعبه
            branch_modem_ip = branch.modem_ip
            if not branch_modem_ip:
                print(f"❌ IP مودم برای شعبه {branch.name} تنظیم نشده است")
                return JsonResponse({
                    'status': 'error',
                    'message': f'IP مودم برای شعبه {branch.name} تنظیم نشده است'
                })

            # تبدیل تومان به ریال (ضرب در 10)
            amount_rial = int(amount_toman) * 10
            print(f"💸 تبدیل مبلغ: {amount_toman} تومان → {amount_rial} ریال")
            print(f"📡 IP مودم شعبه: {branch_modem_ip}")

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
            pos_result = send_to_pos(branch_modem_ip, pos_port, amount_rial)

            if pos_result['status'] == 'success':
                print(f"✅ پرداخت POS موفقیت‌آمیز بود")
                return JsonResponse({
                    'status': 'success',
                    'message': 'مبلغ با موفقیت به دستگاه پوز ارسال شد',
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
                print(f"❌ خطا در پرداخت POS: {pos_result['message']}")
                return JsonResponse({
                    'status': 'error',
                    'message': pos_result['message']
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
@login_required
@csrf_exempt
def finalize_invoice(request):
    """ویوی نهایی کردن و ثبت فاکتور فروش - نسخه بهبود یافته"""
    print("🔴 1 - تابع finalize_invoice فراخوانی شد")

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action', 'save_only')
            paid_amount = data.get('paid_amount', 0)

            # بررسی وجود شعبه در session
            branch_id = request.session.get('branch_id')
            if not branch_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'شعبه انتخاب نشده است. لطفا ابتدا شعبه را انتخاب کنید.'
                })

            # بررسی وجود آیتم در فاکتور
            items = request.session.get('invoice_items', [])
            if not items:
                return JsonResponse({
                    'status': 'error',
                    'message': 'فاکتور خالی است. لطفا ابتدا کالاهایی به فاکتور اضافه کنید.'
                })

            branch = get_object_or_404(Branch, id=branch_id)
            payment_method = request.session.get('payment_method', 'pos')

            # محاسبه دقیق مبالغ
            total_without_discount = sum(item['total'] for item in items)
            items_discount = sum(item.get('discount', 0) for item in items)
            invoice_discount = request.session.get('discount', 0)
            total_discount = items_discount + invoice_discount
            total_amount = max(0, total_without_discount - total_discount)

            print(f"💰 مبلغ کل: {total_amount}, تخفیف: {total_discount}")

            # بررسی موجودی هر آیتم قبل از ثبت نهایی
            stock_errors = []
            for index, item_data in enumerate(items, 1):
                try:
                    product = InventoryCount.objects.get(id=item_data['product_id'], branch=branch)
                    if product.quantity < item_data['quantity']:
                        stock_errors.append(
                            f"ردیف {index}: کالای '{product.product_name}'. موجودی: {product.quantity}, درخواستی: {item_data['quantity']}"
                        )
                except InventoryCount.DoesNotExist:
                    stock_errors.append(f"ردیف {index}: کالا یافت نشد (ID: {item_data['product_id']})")

            if stock_errors:
                error_message = "موجودی برخی کالاها کافی نیست:\n" + "\n".join(stock_errors)
                return JsonResponse({
                    'status': 'error',
                    'message': error_message,
                    'stock_errors': stock_errors
                })

            # اگر روش پرداخت POS است، مبلغ را به دستگاه پوز ارسال کن
            # اگر روش پرداخت POS است، مبلغ را به دستگاه پوز ارسال کن
            # این بخش را در تابع finalize_invoice قرار دهید:

            # اگر روش پرداخت POS است، مبلغ را به دستگاه پوز ارسال کن
            # در تابع finalize_invoice، بخش پرداخت POS را اینگونه تغییر دهید:

            # اگر روش پرداخت POS است، مبلغ را به دستگاه پوز ارسال کن
            if payment_method == 'pos':
                print(f"🎯 روش پرداخت: POS")
                pos_device_id = request.session.get('pos_device_id')

                if not pos_device_id:
                    print(f"❌ هیچ دستگاه پوزی در session وجود ندارد")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'هیچ دستگاه پوزی انتخاب نشده است'
                    })

                print(f"📟 دستگاه پوز انتخاب شده: {pos_device_id}")

                try:
                    pos_device = POSDevice.objects.get(id=pos_device_id, is_active=True)
                    print(f"✅ دستگاه پوز یافت شد: {pos_device.name}")

                    # 🔴 دریافت IP مودم از شعبه
                    branch_modem_ip = branch.modem_ip
                    if not branch_modem_ip:
                        print(f"❌ IP مودم برای شعبه {branch.name} تنظیم نشده است")
                        return JsonResponse({
                            'status': 'error',
                            'message': f'IP مودم برای شعبه {branch.name} تنظیم نشده است. لطفا با مدیر سیستم تماس بگیرید.'
                        })

                    print(f"📡 IP مودم شعبه: {branch_modem_ip}")

                    # تبدیل تومان به ریال (ضرب در 10)
                    amount_rial = total_amount * 10
                    print(f"💸 تبدیل مبلغ فاکتور:")
                    print(f"   شعبه: {branch.name}")
                    print(f"   تومان: {total_amount:,}")
                    print(f"   ریال: {amount_rial:,}")

                    # دریافت پورت از دستگاه پوز
                    pos_port = getattr(pos_device, 'port', 1362)

                    print(f"📍 اطلاعات اتصال:")
                    print(f"   شعبه: {branch.name}")
                    print(f"   دستگاه پوز: {pos_device.name}")
                    print(f"   IP مودم: {branch_modem_ip}")
                    print(f"   پورت: {pos_port}")

                    # 🔴 ارسال مبلغ ریال به دستگاه پوز با استفاده از IP مودم شعبه
                    print(f"🚀 شروع ارسال مبلغ به دستگاه پوز...")
                    pos_result = send_to_pos(branch_modem_ip, pos_port, amount_rial)

                    if pos_result['status'] != 'success':
                        print(f"❌ خطا در ارسال به پوز: {pos_result['message']}")
                        return JsonResponse({
                            'status': 'error',
                            'message': f'خطا در ارتباط با دستگاه پوز: {pos_result["message"]}'
                        })
                    else:
                        print(f"✅ مبلغ با موفقیت به پوز ارسال شد")
                        print(f"📋 پاسخ پوز: {pos_result.get('debug', {}).get('response', 'بدون پاسخ')}")

                except POSDevice.DoesNotExist:
                    print(f"❌ دستگاه پوز با ID {pos_device_id} یافت نشد")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'دستگاه پوز انتخاب شده یافت نشد'
                    })
                except Exception as e:
                    print(f"❌ خطای غیرمنتظره در پردازش POS: {e}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'خطا در پردازش پرداخت POS: {str(e)}'
                    })
            # ایجاد فاکتور اصلی با فیلد paid_amount
            invoice = Invoicefrosh.objects.create(
                branch=branch,
                created_by=request.user,
                total_amount=total_amount,
                discount=invoice_discount,
                total_without_discount=total_without_discount,
                payment_method=payment_method,
                customer_name=request.session.get('customer_name', ''),
                customer_phone=request.session.get('customer_phone', ''),
                is_finalized=True,
                is_paid=True if payment_method in ['cash', 'pos'] else False,
                paid_amount=paid_amount or total_amount,
                payment_date=timezone.now() if payment_method in ['cash', 'pos'] else None
            )

            print(f"✅ فاکتور اصلی ایجاد شد - ID: {invoice.id}, مبلغ پرداخت شده: {paid_amount}")

            # ثبت دستگاه POS اگر روش پرداخت POS باشد
            if payment_method == 'pos':
                pos_device_id = request.session.get('pos_device_id')
                if pos_device_id:
                    try:
                        pos_device = POSDevice.objects.get(id=pos_device_id, is_active=True)
                        invoice.pos_device = pos_device
                        invoice.save()
                        print(f"✅ دستگاه پوز ثبت شد: {pos_device.name}")
                    except POSDevice.DoesNotExist:
                        default_pos = POSDevice.objects.filter(is_default=True, is_active=True).first()
                        if default_pos:
                            invoice.pos_device = default_pos
                            invoice.save()
                            print(f"✅ دستگاه پوز پیش‌فرض ثبت شد: {default_pos.name}")

            # ایجاد آیتم‌های فاکتور و به روزرسانی موجودی
            for item_index, item_data in enumerate(items, 1):
                try:
                    product = InventoryCount.objects.get(id=item_data['product_id'], branch=branch)

                    # محاسبه قیمت‌های دقیق
                    item_total = item_data['price'] * item_data['quantity']
                    item_discount = item_data.get('discount', 0)
                    item_final_price = item_total - item_discount

                    # ایمن‌سازی بیشتر برای دریافت standard_price
                    standard_price_value = item_data['price']

                    try:
                        product_pricing = ProductPricing.objects.filter(
                            product_name=product.product_name
                        ).first()

                        if product_pricing and product_pricing.standard_price is not None:
                            standard_price_value = float(product_pricing.standard_price)
                            print(f"✅ قیمت معیار از ProductPricing گرفته شد: {standard_price_value}")
                        else:
                            print(f"⚠️ قیمت معیار یافت نشد، از قیمت فروش استفاده می‌شود: {standard_price_value}")

                    except Exception as pricing_error:
                        print(f"⚠️ خطا در جستجوی ProductPricing: {str(pricing_error)}")

                    # ایجاد آیتم فاکتور
                    invoice_item = InvoiceItemfrosh(
                        invoice=invoice,
                        product=product,
                        quantity=item_data['quantity'],
                        price=item_data['price'],
                        total_price=item_total,
                        discount=item_discount,
                        standard_price=standard_price_value
                    )
                    invoice_item.save()

                    print(f"✅ آیتم فاکتور با موفقیت ایجاد شد - Standard Price: {standard_price_value}")

                    # به روزرسانی موجودی انبار (کسر کردن)
                    old_quantity = product.quantity
                    product.quantity -= item_data['quantity']
                    product.save()

                    print(
                        f"✅ آیتم {item_index}: {product.product_name} - تعداد: {item_data['quantity']} - موجودی قدیم: {old_quantity} → جدید: {product.quantity}")

                except InventoryCount.DoesNotExist:
                    print(f"❌ خطا در آیتم {item_index}: محصول یافت نشد (ID: {item_data['product_id']})")
                    continue
                except Exception as e:
                    print(f"❌ خطا در آیتم {item_index}: {str(e)}")
                    continue

            # ثبت اطلاعات پرداخت چک
            if payment_method == 'check':
                check_data = request.session.get('check_payment_data')
                if check_data:
                    try:
                        # تبدیل تاریخ چک از رشته شمسی به آبجکت تاریخ میلادی
                        check_date_str = check_data['check_date']
                        print(f"📅 تاریخ چک دریافتی: {check_date_str}")

                        # تبدیل تاریخ شمسی به میلادی
                        try:
                            if '/' in check_date_str:
                                year, month, day = map(int, check_date_str.split('/'))
                                jalali_date = jdatetime.date(year, month, day)
                                gregorian_date = jalali_date.togregorian()
                                check_date = gregorian_date
                                print(f"✅ تاریخ تبدیل شده: {jalali_date} → {gregorian_date}")
                            else:
                                check_date = datetime.strptime(check_date_str, '%Y-%m-%d').date()
                        except Exception as date_error:
                            print(f"❌ خطا در تبدیل تاریخ: {date_error}")
                            check_date = timezone.now().date()
                            print(f"⚠️ از تاریخ امروز استفاده شد: {check_date}")

                        # پیدا کردن دستگاه پوز اگر روش پرداخت باقیمانده POS باشد
                        remaining_pos_device = None
                        if check_data.get('remaining_payment_method') == 'pos' and check_data.get(
                                'remaining_pos_device_id'):
                            try:
                                remaining_pos_device = POSDevice.objects.get(
                                    id=check_data['remaining_pos_device_id'],
                                    is_active=True
                                )
                                print(f"✅ دستگاه پوز برای باقیمانده: {remaining_pos_device.name}")
                            except POSDevice.DoesNotExist:
                                print("⚠️ دستگاه پوز برای باقیمانده یافت نشد")

                        # ثبت اطلاعات چک در دیتابیس
                        print("📋 در حال ثبت اطلاعات چک در دیتابیس...")
                        check_payment = CheckPayment.objects.create(
                            invoice=invoice,
                            owner_name=check_data['owner_name'],
                            owner_family=check_data['owner_family'],
                            national_id=check_data['national_id'],
                            address=check_data.get('address', ''),
                            phone=check_data['phone'],
                            check_number=check_data['check_number'],
                            amount=check_data['amount'],
                            remaining_amount=check_data.get('remaining_amount', 0),
                            remaining_payment_method=check_data.get('remaining_payment_method', 'cash'),
                            pos_device=remaining_pos_device,
                            check_date=check_date
                        )

                        # به‌روزرسانی مبلغ پرداخت شده برای چک
                        invoice.paid_amount = check_data['amount']
                        invoice.is_paid = False  # چک به صورت پیش‌فرض پرداخت نشده در نظر گرفته می‌شود
                        invoice.payment_date = None
                        invoice.save()

                        print(f"✅ اطلاعات چک با موفقیت ثبت شد - ID: {check_payment.id}")
                        print(
                            f"📊 جزئیات چک: {check_data['owner_name']} {check_data['owner_family']} - مبلغ: {check_data['amount']}")

                    except Exception as e:
                        print(f"❌ خطا در ثبت اطلاعات چک: {str(e)}")
                        import traceback
                        print(f"📋 جزئیات خطا:\n{traceback.format_exc()}")
                else:
                    print("⚠️ اطلاعات چک در session وجود ندارد")

            # ثبت اطلاعات پرداخت نسیه
            elif payment_method == 'credit':
                credit_data = request.session.get('credit_payment_data')
                if credit_data:
                    try:
                        # تبدیل تاریخ سررسید
                        due_date_str = credit_data['due_date']
                        if '/' in due_date_str:
                            year, month, day = map(int, due_date_str.split('/'))
                            jalali_date = jdatetime.date(year, month, day)
                            gregorian_date = jalali_date.togregorian()
                            due_date = gregorian_date
                        else:
                            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

                        # پیدا کردن دستگاه پوز اگر روش پرداخت باقیمانده POS باشد
                        remaining_pos_device = None
                        if credit_data.get('remaining_payment_method') == 'pos' and credit_data.get(
                                'remaining_pos_device_id'):
                            try:
                                remaining_pos_device = POSDevice.objects.get(
                                    id=credit_data['remaining_pos_device_id'],
                                    is_active=True
                                )
                            except POSDevice.DoesNotExist:
                                pass

                        # ثبت اطلاعات نسیه
                        credit_payment = CreditPayment.objects.create(
                            invoice=invoice,
                            customer_name=credit_data['customer_name'],
                            customer_family=credit_data['customer_family'],
                            national_id=credit_data['national_id'],
                            address=credit_data.get('address', ''),
                            phone=credit_data['phone'],
                            credit_amount=credit_data.get('credit_amount', 0),
                            remaining_amount=credit_data.get('remaining_amount', 0),
                            remaining_payment_method=credit_data.get('remaining_payment_method', 'cash'),
                            pos_device=remaining_pos_device,
                            due_date=due_date
                        )

                        # به‌روزرسانی مبلغ پرداخت شده برای نسیه
                        invoice.paid_amount = credit_data.get('credit_amount', 0)
                        invoice.is_paid = False  # نسیه به صورت پیش‌فرض پرداخت نشده در نظر گرفته می‌شود
                        invoice.payment_date = None
                        invoice.save()

                        print(f"✅ اطلاعات نسیه ثبت شد - مبلغ: {credit_data.get('credit_amount', 0)}")

                    except Exception as e:
                        print(f"❌ خطا در ثبت اطلاعات نسیه: {str(e)}")

            # پاکسازی session
            session_keys_to_remove = [
                'invoice_items', 'customer_name', 'customer_phone',
                'payment_method', 'discount', 'pos_device_id',
                'check_payment_data', 'credit_payment_data'
            ]

            for key in session_keys_to_remove:
                if key in request.session:
                    del request.session[key]
                    print(f"✅ حذف شده از session: {key}")

            request.session.modified = True

            print(f"🎉 فاکتور {invoice.id} با موفقیت ثبت شد!")
            print(f"📊 خلاصه فاکتور:")
            print(f"   - مبلغ کل: {total_amount}")
            print(f"   - مبلغ پرداخت شده: {paid_amount or total_amount}")
            print(f"   - روش پرداخت: {payment_method}")
            print(f"   - وضعیت پرداخت: {'پرداخت شده' if invoice.is_paid else 'در انتظار پرداخت'}")

            return JsonResponse({
                'status': 'success',
                'message': 'فاکتور با موفقیت ثبت شد',
                'invoice_id': invoice.id,
                'invoice_number': invoice.serial_number,
                'total_amount': total_amount,
                'paid_amount': paid_amount or total_amount,
                'items_count': len(items),
                'payment_method': payment_method,
                'is_paid': invoice.is_paid,
                'customer_name': invoice.customer_name or 'نامشخص',
                'reset_required': True
            })

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"❌ خطای غیرمنتظره در ثبت فاکتور: {str(e)}")
            print(f"📋 جزئیات خطا:\n{error_traceback}")

            return JsonResponse({
                'status': 'error',
                'message': f'خطای غیرمنتظره در ثبت فاکتور: {str(e)}',
                'debug_info': 'لطفا با پشتیبانی تماس بگیرید'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'درخواست نامعتبر. لطفا از فرم صحیح استفاده کنید.'
    })