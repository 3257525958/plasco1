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

@require_GET
def search_invoice(request):
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'error': 'لطفاً حداقل ۲ کاراکتر وارد کنید'}, status=400)

    try:
        # جستجو در تمام فیلدهای مربوط به Invoice و Froshande
        invoices = Invoice.objects.filter(
            Q(serial_number__icontains=query) |
            Q(seller__name__icontains=query) |
            Q(seller__family__icontains=query) |
            Q(seller__store_name__icontains=query) |
            Q(seller__address__icontains=query) |
            Q(items__product__name__icontains=query) |
            Q(items__product_name__icontains=query)
        ).distinct()

        if not invoices.exists():
            return JsonResponse({'error': 'فاکتور یافت نشد'}, status=404)

        # اولین فاکتور یافت شده را برمی‌گردانیم
        invoice = invoices.first()

        items = []
        for item in invoice.items.all():
            # محاسبه موجودی کل برای هر محصول
            total_inventory = Inventory.objects.filter(
                product=item.product
            ).aggregate(total=Sum('quantity'))['total'] or 0

            items.append({
                'id': item.id,
                'product_id': item.product.id if item.product else None,
                'product_name': item.product.name if item.product else item.product_name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_inventory': total_inventory,
            })

        return JsonResponse({
            'invoice': {
                'id': invoice.id,
                'serial_number': invoice.serial_number,
                'seller': str(invoice.seller),
                'date': invoice.date.strftime('%Y-%m-%d'),
            },
            'items': items
        })

    except Exception as e:
        return JsonResponse({'error': f'خطا در جستجو: {str(e)}'}, status=500)

# بقیه توابع بدون تغییر می‌مانند
@require_POST
@csrf_exempt
@transaction.atomic
def update_inventory(request):
    try:
        data = json.loads(request.body)
        items = data.get('items', [])

        if not items:
            return JsonResponse({'error': 'هیچ آیتمی برای ثبت وجود ندارد'}, status=400)

        for item_data in items:
            item_id = item_data['item_id']
            distributions = item_data.get('distributions', [])

            if not distributions:
                continue

            invoice_item = InvoiceItem.objects.get(id=item_id)

            total_distributed = sum(int(dist['quantity']) for dist in distributions)
            if total_distributed > invoice_item.quantity:
                return JsonResponse({'error': f'تعداد توزیع شده برای کالای {invoice_item.product.name} بیشتر از تعداد فاکتور است'}, status=400)

            for distribution in distributions:
                branch_id = distribution['branch_id']
                quantity = int(distribution['quantity'])

                if quantity <= 0:
                    continue

                branch = None
                if branch_id != 'main':
                    branch = Branch.objects.get(id=branch_id)

                inventory, created = Inventory.objects.get_or_create(
                    product=invoice_item.product,
                    branch=branch,
                    defaults={'quantity': quantity}
                )

                if not created:
                    inventory.quantity += quantity
                    inventory.save()

                InventoryHistory.objects.create(
                    product=invoice_item.product,
                    from_branch=None,
                    to_branch=branch,
                    quantity=quantity,
                    action='add',
                    description=f'افزودن موجودی از فاکتور {invoice_item.invoice.serial_number}'
                )

        return JsonResponse({'success': True, 'message': 'موجودی با موفقیت ثبت شد'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_branch_inventory(request, branch_id):
    try:
        if branch_id == 'main':
            inventory_items = Inventory.objects.filter(branch__isnull=True)
            branch_name = 'انبار اصلی'
        else:
            branch = Branch.objects.get(id=branch_id)
            inventory_items = Inventory.objects.filter(branch=branch)
            branch_name = branch.name

        items = []
        for item in inventory_items:
            items.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'last_updated': item.last_updated.strftime('%Y-%m-%d %H:%M')
            })

        return JsonResponse({
            'branch_name': branch_name,
            'items': items
        })

    except Branch.DoesNotExist:
        return JsonResponse({'error': 'شعبه یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_product_inventory(request, product_id):
    try:
        product = Product.objects.get(id=product_id)

        main_inventory = Inventory.objects.filter(
            product=product,
            branch__isnull=True
        ).first()

        branch_inventory = Inventory.objects.filter(
            product=product,
            branch__isnull=False
        ).select_related('branch')

        result = {
            'product_name': product.name,
            'main_inventory': main_inventory.quantity if main_inventory else 0,
            'branches': []
        }

        for item in branch_inventory:
            result['branches'].append({
                'branch_name': item.branch.name,
                'quantity': item.quantity
            })

        return JsonResponse(result)

    except Product.DoesNotExist:
        return JsonResponse({'error': 'کالا یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@csrf_exempt
@transaction.atomic
def transfer_inventory(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        from_branch_id = data.get('from_branch_id')
        to_branch_id = data.get('to_branch_id')
        quantity = int(data.get('quantity', 0))

        if quantity <= 0:
            return JsonResponse({'error': 'تعداد باید بیشتر از صفر باشد'}, status=400)

        product = Product.objects.get(id=product_id)

        if from_branch_id == 'main':
            from_inventory = Inventory.objects.get(product=product, branch__isnull=True)
        else:
            from_branch = Branch.objects.get(id=from_branch_id)
            from_inventory = Inventory.objects.get(product=product, branch=from_branch)

        if from_inventory.quantity < quantity:
            return JsonResponse({'error': 'موجودی کافی نیست'}, status=400)

        from_inventory.quantity -= quantity
        from_inventory.save()

        if to_branch_id == 'main':
            to_inventory, created = Inventory.objects.get_or_create(
                product=product,
                branch__isnull=True,
                defaults={'quantity': quantity}
            )
        else:
            to_branch = Branch.objects.get(id=to_branch_id)
            to_inventory, created = Inventory.objects.get_or_create(
                product=product,
                branch=to_branch,
                defaults={'quantity': quantity}
            )

        if not created:
            to_inventory.quantity += quantity
            to_inventory.save()

        from_branch_obj = None if from_branch_id == 'main' else Branch.objects.get(id=from_branch_id)
        to_branch_obj = None if to_branch_id == 'main' else Branch.objects.get(id=to_branch_id)

        InventoryHistory.objects.create(
            product=product,
            from_branch=from_branch_obj,
            to_branch=to_branch_obj,
            quantity=quantity,
            action='transfer',
            description='انتقال بین شعب'
        )

        return JsonResponse({'success': True, 'message': 'انتقال با موفقیت انجام شد'})

    except (Product.DoesNotExist, Branch.DoesNotExist, Inventory.DoesNotExist) as e:
        return JsonResponse({'error': 'آیتم مورد نظر یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def search_products(request):
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'error': 'لطفاً حداقل ۲ کاراکتر وارد کنید'}, status=400)

    try:
        products = Product.objects.filter(name__icontains=query)[:10]

        results = []
        for product in products:
            total_inventory = Inventory.objects.filter(
                product=product
            ).aggregate(total=Sum('quantity'))['total'] or 0

            results.append({
                'id': product.id,
                'name': product.name,
                'total_inventory': total_inventory
            })

        return JsonResponse({'products': results})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)