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
# @require_GET
# def search_invoice(request):
#     query = request.GET.get('q', '').strip()
#
#     if len(query) < 2:
#         return JsonResponse({'error': 'لطفاً حداقل ۲ کاراکتر وارد کنید'}, status=400)
#
#     try:
#         # جستجو در تمام فیلدهای مربوط به Invoice و Froshande
#         invoices = Invoice.objects.filter(
#             Q(serial_number__icontains=query) |
#             Q(seller__name__icontains=query) |
#             Q(seller__family__icontains=query) |
#             Q(seller__store_name__icontains=query) |
#             Q(seller__address__icontains=query) |
#             Q(items__product__name__icontains=query) |
#             Q(items__product_name__icontains=query)
#         ).distinct()
#
#         if not invoices.exists():
#             return JsonResponse({'error': 'فاکتور یافت نشد'}, status=404)
#
#         # اولین فاکتور یافت شده را برمی‌گردانیم
#         invoice = invoices.first()
#
#         items = []
#         for item in invoice.items.all():
#             # محاسبه موجودی کل برای هر محصول
#             total_inventory = Inventory.objects.filter(
#                 product=item.product
#             ).aggregate(total=Sum('quantity'))['total'] or 0
#
#             items.append({
#                 'id': item.id,
#                 'product_id': item.product.id if item.product else None,
#                 'product_name': item.product.name if item.product else item.product_name,
#                 'quantity': item.quantity,
#                 'unit_price': str(item.unit_price),
#                 'total_inventory': total_inventory,
#             })
#
#         return JsonResponse({
#             'invoice': {
#                 'id': invoice.id,
#                 'serial_number': invoice.serial_number,
#                 'seller': str(invoice.seller),
#                 'date': invoice.date.strftime('%Y-%m-%d'),
#             },
#             'items': items
#         })
#
#     except Exception as e:
#         return JsonResponse({'error': f'خطا در جستجو: {str(e)}'}, status=500)
#
# # بقیه توابع بدون تغییر می‌مانند
# @require_POST
# @csrf_exempt
# @transaction.atomic
# def update_inventory(request):
#     try:
#         data = json.loads(request.body)
#         items = data.get('items', [])
#
#         if not items:
#             return JsonResponse({'error': 'هیچ آیتمی برای ثبت وجود ندارد'}, status=400)
#
#         for item_data in items:
#             item_id = item_data['item_id']
#             distributions = item_data.get('distributions', [])
#
#             if not distributions:
#                 continue
#
#             invoice_item = InvoiceItem.objects.get(id=item_id)
#
#             total_distributed = sum(int(dist['quantity']) for dist in distributions)
#             if total_distributed > invoice_item.quantity:
#                 return JsonResponse({'error': f'تعداد توزیع شده برای کالای {invoice_item.product.name} بیشتر از تعداد فاکتور است'}, status=400)
#
#             for distribution in distributions:
#                 branch_id = distribution['branch_id']
#                 quantity = int(distribution['quantity'])
#
#                 if quantity <= 0:
#                     continue
#
#                 branch = None
#                 if branch_id != 'main':
#                     branch = Branch.objects.get(id=branch_id)
#
#                 inventory, created = Inventory.objects.get_or_create(
#                     product=invoice_item.product,
#                     branch=branch,
#                     defaults={'quantity': quantity}
#                 )
#
#                 if not created:
#                     inventory.quantity += quantity
#                     inventory.save()
#
#                 InventoryHistory.objects.create(
#                     product=invoice_item.product,
#                     from_branch=None,
#                     to_branch=branch,
#                     quantity=quantity,
#                     action='add',
#                     description=f'افزودن موجودی از فاکتور {invoice_item.invoice.serial_number}'
#                 )
#
#         return JsonResponse({'success': True, 'message': 'موجودی با موفقیت ثبت شد'})
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
#
# @require_GET
# def get_branch_inventory(request, branch_id):
#     try:
#         if branch_id == 'main':
#             inventory_items = Inventory.objects.filter(branch__isnull=True)
#             branch_name = 'انبار اصلی'
#         else:
#             branch = Branch.objects.get(id=branch_id)
#             inventory_items = Inventory.objects.filter(branch=branch)
#             branch_name = branch.name
#
#         items = []
#         for item in inventory_items:
#             items.append({
#                 'product_id': item.product.id,
#                 'product_name': item.product.name,
#                 'quantity': item.quantity,
#                 'last_updated': item.last_updated.strftime('%Y-%m-%d %H:%M')
#             })
#
#         return JsonResponse({
#             'branch_name': branch_name,
#             'items': items
#         })
#
#     except Branch.DoesNotExist:
#         return JsonResponse({'error': 'شعبه یافت نشد'}, status=404)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
#
# @require_GET
# def get_product_inventory(request, product_id):
#     try:
#         product = Product.objects.get(id=product_id)
#
#         main_inventory = Inventory.objects.filter(
#             product=product,
#             branch__isnull=True
#         ).first()
#
#         branch_inventory = Inventory.objects.filter(
#             product=product,
#             branch__isnull=False
#         ).select_related('branch')
#
#         result = {
#             'product_name': product.name,
#             'main_inventory': main_inventory.quantity if main_inventory else 0,
#             'branches': []
#         }
#
#         for item in branch_inventory:
#             result['branches'].append({
#                 'branch_name': item.branch.name,
#                 'quantity': item.quantity
#             })
#
#         return JsonResponse(result)
#
#     except Product.DoesNotExist:
#         return JsonResponse({'error': 'کالا یافت نشد'}, status=404)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
#
# @require_POST
# @csrf_exempt
# @transaction.atomic
# def transfer_inventory(request):
#     try:
#         data = json.loads(request.body)
#         product_id = data.get('product_id')
#         from_branch_id = data.get('from_branch_id')
#         to_branch_id = data.get('to_branch_id')
#         quantity = int(data.get('quantity', 0))
#
#         if quantity <= 0:
#             return JsonResponse({'error': 'تعداد باید بیشتر از صفر باشد'}, status=400)
#
#         product = Product.objects.get(id=product_id)
#
#         if from_branch_id == 'main':
#             from_inventory = Inventory.objects.get(product=product, branch__isnull=True)
#         else:
#             from_branch = Branch.objects.get(id=from_branch_id)
#             from_inventory = Inventory.objects.get(product=product, branch=from_branch)
#
#         if from_inventory.quantity < quantity:
#             return JsonResponse({'error': 'موجودی کافی نیست'}, status=400)
#
#         from_inventory.quantity -= quantity
#         from_inventory.save()
#
#         if to_branch_id == 'main':
#             to_inventory, created = Inventory.objects.get_or_create(
#                 product=product,
#                 branch__isnull=True,
#                 defaults={'quantity': quantity}
#             )
#         else:
#             to_branch = Branch.objects.get(id=to_branch_id)
#             to_inventory, created = Inventory.objects.get_or_create(
#                 product=product,
#                 branch=to_branch,
#                 defaults={'quantity': quantity}
#             )
#
#         if not created:
#             to_inventory.quantity += quantity
#             to_inventory.save()
#
#         from_branch_obj = None if from_branch_id == 'main' else Branch.objects.get(id=from_branch_id)
#         to_branch_obj = None if to_branch_id == 'main' else Branch.objects.get(id=to_branch_id)
#
#         InventoryHistory.objects.create(
#             product=product,
#             from_branch=from_branch_obj,
#             to_branch=to_branch_obj,
#             quantity=quantity,
#             action='transfer',
#             description='انتقال بین شعب'
#         )
#
#         return JsonResponse({'success': True, 'message': 'انتقال با موفقیت انجام شد'})
#
#     except (Product.DoesNotExist, Branch.DoesNotExist, Inventory.DoesNotExist) as e:
#         return JsonResponse({'error': 'آیتم مورد نظر یافت نشد'}, status=404)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
#
# @require_GET
# def search_product(request):
#     query = request.GET.get('q', '').strip()
#
#     if len(query) < 2:
#         return JsonResponse({'error': 'لطفاً حداقل ۲ کاراکتر وارد کنید'}, status=400)
#
#     try:
#         products = Product.objects.filter(name__icontains=query)[:10]
#
#         results = []
#         for product in products:
#             total_inventory = Inventory.objects.filter(
#                 product=product
#             ).aggregate(total=Sum('quantity'))['total'] or 0
#
#             results.append({
#                 'id': product.id,
#                 'name': product.name,
#                 'total_inventory': total_inventory
#             })
#
#         return JsonResponse({'products': results})
#
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
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

            for item in items:
                # ایجاد یا به روزرسانی رکورد شمارش
                inventory_count, created = InventoryCount.objects.update_or_create(
                    product_name=item['productName'],
                    branch_id=item['branchId'],
                    defaults={
                        'is_new': item['productType'] == 'new',
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



# Search invoices by seller name, family or invoice serial number
# def search_invoices(request):
#     print('1')
#     try:
#         query = request.GET.get('q', '')
#
#         # تبدیل اعداد فارسی/عربی به انگلیسی در صورت نیاز
#         query_english = convert_persian_arabic_to_english(query)
#
#         if len(query_english) < 2:
#             return JsonResponse({'results': []})
#
#         # جستجو در فاکتورها بر اساس نام فروشنده، نام خانوادگی یا شماره سریال
#         invoices = Invoice.objects.filter(
#             Q(seller__name__icontains=query_english) |
#             Q(seller__family__icontains=query_english) |
#             Q(serial_number__icontains=query_english)
#         ).select_related('seller')[:10]
#
#         results = []
#         for invoice in invoices:
#             results.append({
#                 'id': invoice.id,
#                 'text': f"{invoice.serial_number} - {invoice.seller.name} {invoice.seller.family}",
#                 'serial_number': invoice.serial_number,
#                 'seller_name': f"{invoice.seller.name} {invoice.seller.family}",
#                 'date': invoice.jalali_date
#             })
#
#         return JsonResponse({'results': results})
#
#     except Exception as e:
#         logger.error(f"Error in invoice search: {str(e)}")
#         return JsonResponse({'results': []})

def search_invoices(request):
    try:
        query = request.GET.get('q', '')

        if len(query) < 2:
            return JsonResponse({'results': []})

        # جستجو در فاکتورها بر اساس نام فروشنده، نام خانوادگی یا شماره سریال
        invoices = Invoice.objects.filter(
            Q(seller__name__icontains=query) |
            Q(seller__family__icontains=query) |
            Q(serial_number__icontains=query)
        ).select_related('seller').distinct()[:10]  # محدود کردن به 10 نتیجه

        results = []
        for invoice in invoices:
            results.append({
                'id': invoice.id,
                'text': f"{invoice.serial_number} - {invoice.seller.name} {invoice.seller.family}",
                'serial_number': invoice.serial_number,
                'seller_name': f"{invoice.seller.name} {invoice.seller.family}",
                'date': invoice.jalali_date
            })

        # اضافه کردن log برای دیباگ
        print(f": '{query}' - add {len(results)}")
        logger.info(f"جستجوی فاکتور: '{query}' - تعداد نتایج: {len(results)}")

        return JsonResponse({'results': results})

    except Exception as e:
        logger.error(f"Error in invoice search: {str(e)}")
        return JsonResponse({'results': []})

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


# Store invoice items in inventory0
@method_decorator(csrf_exempt, name='dispatch')
class StoreInvoiceItems(View):
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'error': 'لطفاً ابتدا وارد سیستم شوید'})

            data = json.loads(request.body)
            items = data.get('items', [])

            for item in items:
                branch_id = item.get('branch_id')
                quantity = item.get('quantity')
                product_name = item.get('product_name')

                # Check if branch exists
                try:
                    branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'شعبه با شناسه {branch_id} یافت نشد'})

                # Create or update inventory count
                inventory_count, created = InventoryCount.objects.update_or_create(
                    product_name=product_name,
                    branch=branch,
                    defaults={
                        'quantity': quantity,
                        'counter': request.user,
                        'is_new': True
                    }
                )

            # این خط کلمه success را در logهای Python چاپ می‌کند
            print('succes')
            # یا می‌توانید از print استفاده کنید:
            # print("success")

            return JsonResponse({'success': True, 'message': 'اطلاعات انبار با موفقیت ثبت شد'})

        except Exception as e:
            logger.error(f"Error storing invoice items: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})