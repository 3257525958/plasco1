from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from decimal import Decimal
import json

from account_app.models import InventoryCount, Branch
from .models import Invoicefrosh, InvoiceItemfrosh
from .forms import BranchSelectionForm

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.utils import timezone
from decimal import Decimal
import json

from account_app.models import InventoryCount, Branch, PaymentMethod
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

    if request.method == 'POST' and 'finalize' in request.POST:
        # ثبت نهایی فاکتور
        action = request.POST.get('action')

        if action in ['print_and_save', 'save_only']:
            # ایجاد فاکتور در دیتابیس
            invoice = Invoicefrosh.objects.create(
                branch_id=branch_id,
                created_by=request.user,
                total_amount=0
            )

            # افزودن آیتم‌ها به فاکتور
            items = request.session.get('invoice_items', [])
            total_amount = 0

            for item in items:
                product = get_object_or_404(InventoryCount, id=item['product_id'])
                item_total = product.selling_price * item['quantity']

                InvoiceItemfrosh.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=item['quantity'],
                    price=product.selling_price,
                    total_price=item_total
                )

                # به روز رسانی موجودی انبار
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

            if action == 'print_and_save':
                # انتقال به صفحه چاپ
                return redirect('invoice_app:invoice_print', invoice_id=invoice.id)
            else:
                # انتقال به صفحه انتخاب روش پرداخت
                request.session['invoice_id'] = invoice.id
                return redirect('invoice_app:select_payment_method')

    return render(request, 'invoice_create.html', {
        'branch_selected': True,
        'branch': branch,
        'items': request.session.get('invoice_items', [])
    })


@login_required
def select_payment_method(request):
    invoice_id = request.session.get('invoice_id')
    if not invoice_id:
        return redirect('invoice_app:create_invoice')

    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            invoice.payment_method = payment_method
            invoice.is_paid = True
            invoice.save()

            # پاک کردن invoice_id از session
            del request.session['invoice_id']

            return redirect('invoice_app:invoice_success')
    else:
        # تنظیم روش پرداخت پیش فرض
        default_payment = PaymentMethod.objects.filter(is_default=True, is_active=True).first()
        form = PaymentMethodForm(initial={'payment_method': default_payment})

    return render(request, 'select_payment_method.html', {
        'form': form,
        'invoice': invoice
    })


# سایر ویوها بدون تغییر باقی می‌مانند...




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
                'quantity': product.quantity
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

        # بررسی موجودی کافی
        if product.quantity < quantity:
            return JsonResponse({
                'status': 'error',
                'message': f'موجودی کافی نیست. موجودی فعلی: {product.quantity}'
            })

        # بررسی وجود محصول در سشن
        items = request.session.get('invoice_items', [])
        item_exists = False

        for item in items:
            if item['product_id'] == product_id:
                new_quantity = item['quantity'] + quantity
                if product.quantity < new_quantity:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'موجودی کافی نیست. موجودی فعلی: {product.quantity}'
                    })
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

        # بررسی موجودی کافی
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

        return JsonResponse({
            'status': 'success',
            'items': items,
            'message': 'تعداد کالا با موفقیت به روز شد'
        })

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})