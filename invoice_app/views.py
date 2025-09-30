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

            required_fields = ['owner_name', 'owner_family', 'national_id', 'phone',
                               'check_number', 'amount', 'check_date']

            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'status': 'error', 'message': f'فیلد {field} الزامی است'})

            request.session['check_payment_data'] = {
                'owner_name': data.get('owner_name', '').strip(),
                'owner_family': data.get('owner_family', '').strip(),
                'national_id': data.get('national_id', '').strip(),
                'address': data.get('address', '').strip(),
                'phone': data.get('phone', '').strip(),
                'check_number': data.get('check_number', '').strip(),
                'amount': int(data.get('amount', 0)),
                'check_date': data.get('check_date', '')
            }
            request.session.modified = True

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'})
    return JsonResponse({'status': 'error'})

@login_required
@csrf_exempt
def save_credit_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            required_fields = ['customer_name', 'customer_family', 'phone', 'national_id', 'due_date']

            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'status': 'error', 'message': f'فیلد {field} الزامی است'})

            request.session['credit_payment_data'] = {
                'customer_name': data.get('customer_name', '').strip(),
                'customer_family': data.get('customer_family', '').strip(),
                'phone': data.get('phone', '').strip(),
                'address': data.get('address', '').strip(),
                'national_id': data.get('national_id', '').strip(),
                'due_date': data.get('due_date', '')
            }
            request.session.modified = True

            return JsonResponse({'status': 'success'})
        except Exception as e:
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
@csrf_exempt
def finalize_invoice(request):
    """
    ویوی نهایی کردن و ثبت فاکتور فروش
    این ویو تمام مراحل ثبت فاکتور را انجام می‌دهد
    """
    print("🔴 1 - تابع finalize_invoice فراخوانی شد")

    if request.method == 'POST':
        try:
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
            print(2222222222222222222222222222)
            for index, item_data in enumerate(items, 1):
                try:
                    print(33333333333)
                    product = InventoryCount.objects.get(id=item_data['product_id'], branch=branch)
                    if product.quantity < item_data['quantity']:
                        stock_errors.append(
                            f"ردیف {index}: کالای '{product.product_name}'. موجودی: {product.quantity}, درخواستی: {item_data['quantity']}"
                        )
                except InventoryCount.DoesNotExist:
                    stock_errors.append(f"ردیف {index}: کالا یافت نشد (ID: {item_data['product_id']})")

            # اگر خطای موجودی وجود دارد، به کاربر گزارش دهیم
            if stock_errors:
                print(444444444)
                error_message = "موجودی برخی کالاها کافی نیست:\n" + "\n".join(stock_errors)
                return JsonResponse({
                    'status': 'error',
                    'message': error_message,
                    'stock_errors': stock_errors
                })

            # ایجاد فاکتور اصلی
            print(55555555)
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
                is_paid=True if payment_method in ['cash', 'pos'] else False
            )

            print(f"✅ فاکتور اصلی ایجاد شد - ID: {invoice.id}")

            # ثبت دستگاه POS اگر روش پرداخت POS باشد
            if payment_method == 'pos':
                print(6666666666666)
                pos_device_id = request.session.get('pos_device_id')
                if pos_device_id:
                    try:
                        pos_device = POSDevice.objects.get(id=pos_device_id, is_active=True)
                        invoice.pos_device = pos_device
                        invoice.save()
                        print(f"✅ دستگاه پوز ثبت شد: {pos_device.name}")
                    except POSDevice.DoesNotExist:
                        # اگر دستگاه پیدا نشد، از پیش‌فرض استفاده کن
                        default_pos = POSDevice.objects.filter(is_default=True, is_active=True).first()
                        if default_pos:
                            invoice.pos_device = default_pos
                            invoice.save()
                            print(f"✅ دستگاه پوز پیش‌فرض ثبت شد: {default_pos.name}")
                else:
                    # اگر دستگاه انتخاب نشده، از پیش‌فرض استفاده کن
                    default_pos = POSDevice.objects.filter(is_default=True, is_active=True).first()
                    if default_pos:
                        invoice.pos_device = default_pos
                        invoice.save()
                        print(f"✅ دستگاه پوز پیش‌فرض ثبت شد: {default_pos.name}")

            # ایجاد آیتم‌های فاکتور و به روزرسانی موجودی
            for item_index, item_data in enumerate(items, 1):
                print(777)
                try:
                    print(88888888888888)
                    product = InventoryCount.objects.get(id=item_data['product_id'], branch=branch)

                    # محاسبه قیمت‌های دقیق
                    item_total = item_data['price'] * item_data['quantity']
                    item_discount = item_data.get('discount', 0)
                    item_final_price = item_total - item_discount

                    # ایجاد آیتم فاکتور
                    print(999999999999)
                    try:
                        # ایمن‌سازی بیشتر برای دریافت standard_price
                        standard_price_value = item_data['price']  # مقدار پیش‌فرض

                        # جستجوی ProductPricing با مدیریت خطاهای بهتر
                        try:
                            product_pricing = ProductPricing.objects.filter(
                                product_name=product.product_name
                            ).first()

                            if product_pricing and product_pricing.standard_price is not None:
                                print(product_pricing.standard_price)
                                print(3333333333333333333333333333333333333333333333333333)
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

                    except Exception as e:
                        print(f"❌ خطا در ایجاد آیتم فاکتور: {str(e)}")
                        # در صورت خطا، با مقادیر پایه ایجاد کن
                        try:
                            InvoiceItemfrosh.objects.create(
                                invoice=invoice,
                                product=product,
                                quantity=item_data['quantity'],
                                price=item_data['price'],
                                total_price=item_total,
                                discount=item_discount,
                                standard_price=item_data['price']  # حداقل مقدار
                            )
                            print("✅ آیتم فاکتور با مقادیر پایه ایجاد شد")
                        except Exception as fallback_error:
                            print(f"❌ خطا حتی در ایجاد fallback: {str(fallback_error)}")

                    print(00000000000)
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
                        # تبدیل تاریخ چک از رشته به آبجکت تاریخ
                        check_date = datetime.strptime(check_data['check_date'], '%Y-%m-%d').date()

                        CheckPayment.objects.create(
                            invoice=invoice,
                            owner_name=check_data['owner_name'],
                            owner_family=check_data['owner_family'],
                            national_id=check_data['national_id'],
                            address=check_data.get('address', ''),
                            phone=check_data['phone'],
                            check_number=check_data['check_number'],
                            amount=check_data['amount'],
                            check_date=check_date
                        )
                        print("✅ اطلاعات چک ثبت شد")
                    except Exception as e:
                        print(f"❌ خطا در ثبت اطلاعات چک: {str(e)}")
                else:
                    print("⚠️ اطلاعات چک در session وجود ندارد")

            # ثبت اطلاعات پرداخت نسیه
            elif payment_method == 'credit':
                credit_data = request.session.get('credit_payment_data')
                if credit_data:
                    try:
                        # تبدیل تاریخ سررسید از رشته به آبجکت تاریخ
                        due_date = datetime.strptime(credit_data['due_date'], '%Y-%m-%d').date()

                        CreditPayment.objects.create(
                            invoice=invoice,
                            customer_name=credit_data['customer_name'],
                            customer_family=credit_data['customer_family'],
                            phone=credit_data['phone'],
                            address=credit_data.get('address', ''),
                            national_id=credit_data['national_id'],
                            due_date=due_date
                        )
                        print("✅ اطلاعات نسیه ثبت شد")
                    except Exception as e:
                        print(f"❌ خطا در ثبت اطلاعات نسیه: {str(e)}")
                else:
                    print("⚠️ اطلاعات نسیه در session وجود ندارد")

            # پاک کردن session داده‌های فاکتور جاری
            session_keys_to_remove = [
                'invoice_items', 'customer_name', 'customer_phone',
                'payment_method', 'discount', 'pos_device_id',
                'check_payment_data', 'credit_payment_data'
            ]

            for key in session_keys_to_remove:
                if key in request.session:
                    del request.session[key]
                    print(f"✅ حذف شده از session: {key}")

            # تأیید نهایی که session پاک شده
            request.session.modified = True
            remaining_items = request.session.get('invoice_items', [])
            print(f"✅ تأیید پاکسازی session - آیتم‌های باقیمانده: {len(remaining_items)}")

            # ثبت لاگ نهایی برای پیگیری
            print(f"🎉 فاکتور {invoice.id} با موفقیت ثبت شد!")
            print(f"📊 اطلاعات فاکتور:")
            print(f"   - شماره سریال: {invoice.serial_number}")
            print(f"   - مبلغ کل: {total_amount} تومان")
            print(f"   - تعداد آیتم‌ها: {len(items)}")
            print(f"   - روش پرداخت: {payment_method}")
            print(f"   - مشتری: {request.session.get('customer_name', 'نامشخص')}")

            # بازگشت پاسخ موفق
            return JsonResponse({
                'status': 'success',
                'message': 'فاکتور با موفقیت ثبت شد',
                'invoice_id': invoice.id,
                'invoice_number': invoice.serial_number,
                'total_amount': total_amount,
                'items_count': len(items),
                'payment_method': payment_method,
                'customer_name': invoice.customer_name or 'نامشخص',
                'reset_required': True  # فلگ برای بازنشانی صفحه در کلاینت
            })

        except json.JSONDecodeError as e:
            print(f"❌ خطای JSON: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در پردازش داده‌های ارسالی: {str(e)}'
            })

        except Exception as e:
            # ثبت خطای کامل برای دیباگ
            import traceback
            error_traceback = traceback.format_exc()
            print(f"❌ خطای غیرمنتظره در ثبت فاکتور: {str(e)}")
            print(f"📋 جزئیات خطا:\n{error_traceback}")

            return JsonResponse({
                'status': 'error',
                'message': f'خطای غیرمنتظره در ثبت فاکتور: {str(e)}',
                'debug_info': 'لطفا با پشتیبانی تماس بگیرید'
            })

    # اگر درخواست POST نبود
    print("❌ درخواست غیر POST دریافت شد")
    return JsonResponse({
        'status': 'error',
        'message': 'درخواست نامعتبر. لطفا از فرم صحیح استفاده کنید.'
    })

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