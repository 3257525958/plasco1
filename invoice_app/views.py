from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.utils import timezone
from decimal import Decimal
import json

from account_app.models import InventoryCount, Branch, PaymentMethod, ProductPricing
from .models import Invoicefrosh, InvoiceItemfrosh
from .forms import BranchSelectionForm, PaymentMethodForm


@login_required
def create_invoice(request):
    # همیشه ابتدا شعبه پرسیده شود
    if 'branch_id' not in request.session:
        if request.method == 'POST':
            form = BranchSelectionForm(request.POST)
            if form.is_valid():
                request.session['branch_id'] = form.cleaned_data['branch'].id
                request.session['branch_name'] = form.cleaned_data['branch'].name
                request.session['invoice_items'] = []
                # پاک کردن اطلاعات خریدار قبلی
                if 'customer_name' in request.session:
                    del request.session['customer_name']
                if 'customer_phone' in request.session:
                    del request.session['customer_phone']
                return redirect('invoice_app:create_invoice')
        else:
            form = BranchSelectionForm()

        return render(request, 'invoice_create.html', {
            'form': form,
            'branch_selected': False
        })

    # اگر شعبه انتخاب شده، صفحه اصلی فاکتور نمایش داده شود
    branch_id = request.session.get('branch_id')
    branch_name = request.session.get('branch_name')
    branch = get_object_or_404(Branch, id=branch_id)

    # دریافت روش پرداخت پیش فرض
    last_payment_id = request.session.get('last_payment_method')
    if last_payment_id:
        try:
            default_payment = PaymentMethod.objects.get(id=last_payment_id)
        except PaymentMethod.DoesNotExist:
            default_payment = PaymentMethod.objects.filter(is_default=True, is_active=True).first()
    else:
        default_payment = PaymentMethod.objects.filter(is_default=True, is_active=True).first()

    if request.method == 'POST' and 'finalize' in request.POST:
        # ثبت نهایی فاکتور
        action = request.POST.get('action')

        if action in ['print_and_save', 'save_only']:
            # دریافت اطلاعات خریدار از session
            customer_name = request.session.get('customer_name', '')
            customer_phone = request.session.get('customer_phone', '')

            # دریافت روش پرداخت از session
            payment_method_id = request.session.get('last_payment_method')
            payment_method = None
            if payment_method_id:
                try:
                    payment_method = PaymentMethod.objects.get(id=payment_method_id)
                except PaymentMethod.DoesNotExist:
                    pass

            # اگر روش پرداخت پیدا نشد، از پیش فرض استفاده کنید
            if not payment_method:
                payment_method = PaymentMethod.objects.filter(is_default=True, is_active=True).first()

            # ایجاد فاکتور در دیتابیس
            invoice = Invoicefrosh.objects.create(
                branch_id=branch_id,
                created_by=request.user,
                total_amount=0,
                customer_name=customer_name,
                customer_phone=customer_phone,
                payment_method=payment_method,
                is_paid=True if payment_method else False
            )

            # افزودن آیتم‌ها به فاکتور
            items = request.session.get('invoice_items', [])
            total_amount = 0

            for item in items:
                product = get_object_or_404(InventoryCount, id=item['product_id'])
                item_total = product.selling_price * item['quantity']

                # دریافت قیمت معیار از مدل ProductPricing با استفاده از product_name
                try:
                    product_pricing = ProductPricing.objects.get(product_name=product.product_name)
                    standard_price = product_pricing.standard_price
                except ProductPricing.DoesNotExist:
                    standard_price = 0

                InvoiceItemfrosh.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=item['quantity'],
                    price=product.selling_price,
                    total_price=item_total,
                    standard_price=standard_price
                )

                # به روز رسانی موجودی انبار (حتی اگر منفی شود)
                product.quantity -= item['quantity']
                product.save()

                total_amount += item_total

            invoice.total_amount = total_amount
            invoice.is_finalized = True
            invoice.save()

            # پاک کردن session
            del request.session['branch_id']
            del request.session['branch_name']
            del request.session['invoice_items']
            if 'customer_name' in request.session:
                del request.session['customer_name']
            if 'customer_phone' in request.session:
                del request.session['customer_phone']

            if action == 'print_and_save':
                # انتقال به صفحه چاپ
                return redirect('invoice_app:invoice_print', invoice_id=invoice.id)
            else:
                # انتقال به صفحه موفقیت
                return redirect('invoice_app:invoice_success')

    return render(request, 'invoice_create.html', {
        'branch_selected': True,
        'branch': branch,
        'items': request.session.get('invoice_items', []),
        'customer_name': request.session.get('customer_name', ''),
        'customer_phone': request.session.get('customer_phone', ''),
        'payment_methods': PaymentMethod.objects.filter(is_active=True),
        'default_payment_method': default_payment
    })


@login_required
@csrf_exempt
def search_product(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '')
        branch_id = request.session.get('branch_id')

        if not branch_id:
            return JsonResponse({'error': 'لطفا ابتدا شعبه را انتخاب کنید'}, status=400)

        # جستجوی کالا بر اساس نام یا بارکد در شعبه انتخاب شده
        products = InventoryCount.objects.filter(
            branch_id=branch_id
        ).filter(
            models.Q(product_name__icontains=query) |
            models.Q(barcode_data__icontains=query)
        )[:10]  # محدود کردن نتایج به 10 مورد

        results = []
        for product in products:
            results.append({
                'id': product.id,
                'name': product.product_name,
                'quantity': product.quantity,
                'low_stock': product.quantity <= 0  # نشانگر برای موجودی کم یا منفی
            })

        return JsonResponse({'results': results})

    return JsonResponse({'error': 'درخواست نامعتبر'}, status=400)


@login_required
@csrf_exempt
def add_item_to_invoice(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        # دریافت اطلاعات محصول
        product = get_object_or_404(InventoryCount, id=product_id)

        # بررسی وجود محصول در سشن
        items = request.session.get('invoice_items', [])
        item_exists = False

        for item in items:
            if item['product_id'] == product_id:
                new_quantity = item['quantity'] + quantity
                item['quantity'] = new_quantity
                item['total'] = product.selling_price * new_quantity
                item_exists = True
                break

        if not item_exists:
            items.append({
                'product_id': product_id,
                'product_name': product.product_name,
                'price': product.selling_price,
                'quantity': quantity,
                'total': product.selling_price * quantity
            })

        request.session['invoice_items'] = items

        return JsonResponse({
            'status': 'success',
            'items': items,
            'message': 'کالا با موفقیت به فاکتور اضافه شد'
        })

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})


@login_required
@csrf_exempt
def remove_item_from_invoice(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')

        items = request.session.get('invoice_items', [])
        items = [item for item in items if item['product_id'] != product_id]

        request.session['invoice_items'] = items

        return JsonResponse({'status': 'success', 'items': items})

    return JsonResponse({'status': 'error'})


@login_required
@csrf_exempt
def save_customer_info(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request.session['customer_name'] = data.get('customer_name', '')
        request.session['customer_phone'] = data.get('customer_phone', '')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})


@login_required
@csrf_exempt
def save_payment_method(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        try:
            payment_method = PaymentMethod.objects.get(id=payment_method_id)
            request.session['last_payment_method'] = payment_method.id
            return JsonResponse({'status': 'success'})
        except PaymentMethod.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'روش پرداخت نامعتبر'})
    return JsonResponse({'status': 'error'})


@login_required
def invoice_success(request):
    return render(request, 'invoice_success.html')


@login_required
def invoice_print(request, invoice_id):
    invoice = get_object_or_404(Invoicefrosh, id=invoice_id)
    return render(request, 'invoice_print.html', {'invoice': invoice})


@login_required
def cancel_invoice(request):
    if 'branch_id' in request.session:
        del request.session['branch_id']
        del request.session['branch_name']
    if 'invoice_items' in request.session:
        del request.session['invoice_items']
    if 'customer_name' in request.session:
        del request.session['customer_name']
    if 'customer_phone' in request.session:
        del request.session['customer_phone']

    return redirect('invoice_app:create_invoice')


@login_required
@csrf_exempt
def update_item_quantity(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        new_quantity = data.get('quantity')

        # دریافت اطلاعات محصول
        product = get_object_or_404(InventoryCount, id=product_id)

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

        return JsonResponse({
            'status': 'success',
            'items': items,
            'message': 'تعداد کالا با موفقیت به روز شد'
        })

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})