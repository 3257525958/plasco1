from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
import math
from dashbord_app.models import Invoice, InvoiceItem
from cantact_app.models import Branch
from account_app.models import InventoryCount
from django.db.models import Max
from decimal import Decimal


def invoice_list(request):
    """
    نمایش لیست فاکتورها
    """
    invoices = Invoice.objects.all().prefetch_related('items')
    return render(request, 'invoice_list.html', {'invoices': invoices})


@require_POST
def reset_remaining_quantity(request):
    """
    ریست کردن تعداد باقیمانده فاکتورهای انتخاب شده
    """
    selected_invoice_ids = request.POST.getlist('selected_invoices')

    if not selected_invoice_ids:
        messages.warning(request, 'هیچ فاکتوری انتخاب نشده است.')
        return redirect('invoice_list')

    try:
        # پیدا کردن آیتم‌های فاکتورهای انتخاب شده
        selected_items = InvoiceItem.objects.filter(invoice_id__in=selected_invoice_ids)
        updated_count = 0

        # آپدیت تعداد باقیمانده
        for item in selected_items:
            if item.remaining_quantity != item.quantity:
                item.remaining_quantity = item.quantity
                item.save(update_fields=['remaining_quantity'])
                updated_count += 1

        if updated_count > 0:
            messages.success(
                request,
                f'تعداد باقیمانده برای {updated_count} آیتم با موفقیت بروزرسانی شد.'
            )
        else:
            messages.info(request, 'همه آیتم‌ها قبلاً بروزرسانی شده بودند.')

    except Exception as e:
        messages.error(request, f'خطا در بروزرسانی: {str(e)}')

    return redirect('invoice_list')


@require_POST
@transaction.atomic
def distribute_inventory(request):
    print(11111111111111111111111111111111111111111111)
    """
    توزیع مساوی کالاهای فاکتورهای انتخاب شده بین شعب - فقط بر اساس remaining_quantity
    """
    selected_invoice_ids = request.POST.getlist('selected_invoices')

    if not selected_invoice_ids:
        messages.warning(request, 'هیچ فاکتوری انتخاب نشده است.')
        return redirect('invoice_list')

    try:
        # دریافت تمام شعب
        branches = list(Branch.objects.all())
        if not branches:
            messages.error(request, 'هیچ شعبه‌ای تعریف نشده است.')
            return redirect('invoice_list')

        branch_count = len(branches)

        # 🔴 تغییر مهم: فقط آیتم‌هایی که remaining_quantity دارند
        all_items = InvoiceItem.objects.filter(
            invoice_id__in=selected_invoice_ids,
            remaining_quantity__gt=0  # فقط باقیمانده‌های بیشتر از صفر
        ).select_related('invoice')

        if not all_items:
            messages.warning(request, 'هیچ کالایی با تعداد باقیمانده برای توزیع یافت نشد.')
            return redirect('invoice_list')

        # گروه‌بندی کالاها بر اساس نام و نوع - فقط remaining_quantity
        product_summary = {}
        for item in all_items:
            key = f"{item.product_name}|{item.product_type}"
            if key not in product_summary:
                product_summary[key] = {
                    'name': item.product_name,
                    'type': item.product_type,
                    'total_remaining': 0,  # 🔴 فقط باقیمانده
                    'max_selling_price': item.selling_price or item.unit_price,
                    'is_new': item.product_type == 'new',
                    'source_items': []
                }
            # 🔴 تغییر: جمع‌زنی remaining_quantity به جای quantity
            product_summary[key]['total_remaining'] += item.remaining_quantity
            product_summary[key]['max_selling_price'] = max(
                product_summary[key]['max_selling_price'],
                item.selling_price or item.unit_price
            )
            product_summary[key]['source_items'].append(item.id)

        # آماده‌سازی داده‌ها برای توزیع
        products_to_distribute = []
        for key, data in product_summary.items():
            if data['total_remaining'] > 0:
                products_to_distribute.append(data)

        if not products_to_distribute:
            messages.warning(request, 'هیچ کالایی با تعداد باقیمانده معتبر برای توزیع یافت نشد.')
            return redirect('invoice_list')

        # 🔴🔴 تغییر جدید: اطمینان از وجود ProductPricing برای هر محصول
        for product in products_to_distribute:
            product_name = product['name']

            try:
                # محاسبه highest_purchase_price از روی فاکتورها
                highest_purchase = InvoiceItem.objects.filter(
                    product_name=product_name,
                    invoice_id__in=selected_invoice_ids
                ).aggregate(max_price=Max('unit_price'))['max_price'] or Decimal('0')

                # استفاده از max_selling_price که قبلاً محاسبه شده
                standard_price = product['max_selling_price']

                ProductPricing.objects.create(
                    product_name=product_name,
                    highest_purchase_price=highest_purchase,
                    standard_price=standard_price
                )

            except ProductPricing.DoesNotExist:
                # اگر وجود نداشت، ایجاد کن
                pass
        # توزیع کالاها بر اساس remaining_quantity
        total_distributed = 0
        distribution_details = []

        for product in products_to_distribute:
            # 🔴 تغییر: استفاده از total_remaining به جای total_quantity
            total_remaining = product['total_remaining']
            base_per_branch = total_remaining // branch_count
            remainder = total_remaining % branch_count

            product_distributed = 0

            for i, branch in enumerate(branches):
                qty_for_branch = base_per_branch
                if i < remainder:
                    qty_for_branch += 1

                if qty_for_branch > 0:
                    # پیدا کردن یا ایجاد رکورد انبار
                    inventory_obj, created = InventoryCount.objects.get_or_create(
                        product_name=product['name'],
                        branch=branch,
                        is_new=product['is_new'],
                        defaults={
                            'quantity': qty_for_branch,
                            'counter': request.user,
                            'selling_price': product['max_selling_price'],
                            'profit_percentage': Decimal('30.00')
                        }
                    )

                    if not created:
                        # به روزرسانی رکورد موجود
                        inventory_obj.quantity += qty_for_branch
                        inventory_obj.selling_price = max(
                            inventory_obj.selling_price or 0,
                            product['max_selling_price']
                        )
                        inventory_obj.save()

                    product_distributed += qty_for_branch
                    total_distributed += qty_for_branch

            distribution_details.append(
                f"{product['name']} ({product['type']}): {product_distributed} عدد"
            )

        # 🔴 تغییر: فقط آیتم‌هایی که remaining_quantity داشتند صفر می‌شوند
        zeroed_count = all_items.update(remaining_quantity=0)

        # پیام موفقیت
        detail_message = "\n".join(distribution_details)
        messages.success(
            request,
            f'✅ توزیع با موفقیت انجام شد!\n\n'
            f'📊 خلاصه عملکرد:\n'
            f'• تعداد کل کالاهای توزیع شده: {total_distributed} عدد\n'
            f'• تعداد کالاهای منحصر به فرد: {len(products_to_distribute)} مورد\n'
            f'• تعداد شعب: {branch_count} شعبه\n'
            f'• آیتم‌های به روز شده: {zeroed_count} مورد\n\n'
            f'📦 جزئیات توزیع:\n{detail_message}'
        )

    except Exception as e:
        messages.error(request, f'❌ خطا در توزیع کالاها: {str(e)}')

    return redirect('invoice_list')


# ---------------------------------------------------------------پاک کردن قیمت ها------------------
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from account_app.models import ProductPricing


def is_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def delete_all_product_pricing(request):
    """
    ویو برای حذف تمام رکوردهای ProductPricing با تأیید کاربر
    """
    print("🔍 1 - ویو فراخوانی شد")

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'confirm':
            # شمارش رکوردها قبل از حذف
            record_count = ProductPricing.objects.count()

            if record_count == 0:
                messages.warning(request, '❌ هیچ رکوردی برای حذف وجود ندارد.')
                return redirect('delete_all_product_pricing')

            try:
                # حذف تمام رکوردها
                deleted_count, deleted_details = ProductPricing.objects.all().delete()
                messages.success(request, f'✅ با موفقیت {deleted_count} رکورد قیمت‌گذاری حذف شد.')

            except Exception as e:
                error_msg = f'❌ خطا در حذف رکوردها: {str(e)}'
                messages.error(request, error_msg)

            return redirect('delete_all_product_pricing')

        elif action == 'cancel':
            messages.info(request, '🔒 عملیات حذف لغو شد.')
            return redirect('delete_all_product_pricing')
        else:
            messages.error(request, '❌ عمل نامعتبر!')
            return redirect('delete_all_product_pricing')

    # GET request - نمایش صفحه تأیید
    record_count = ProductPricing.objects.count()
    context = {
        'record_count': record_count,
        'page_title': 'حذف تمام اطلاعات قیمت‌گذاری',
    }
    return render(request, 'delete_all_product_pricing.html', context)



# ------------------------------------------------------پاک کردن کل دیتاهای انبار------------------------------------------
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from account_app.models import InventoryCount


@require_POST
def clear_inventory(request):
    """
    پاک کردن تمام رکوردهای مدل InventoryCount پس از تأیید کاربر
    """
    try:
        # بررسی وجود رکورد برای نمایش پیام مناسب
        record_count = InventoryCount.objects.count()

        if record_count == 0:
            messages.warning(request, "در حال حاضر هیچ داده‌ای در انبار وجود ندارد.")
        else:
            # پاک کردن تمام رکوردها
            deleted_count = InventoryCount.objects.all().delete()[0]
            messages.success(request, f"✅ تمام داده‌های انبار ({deleted_count} رکورد) با موفقیت پاک شدند.")

    except Exception as e:
        messages.error(request, f"❌ خطا در پاک کردن داده‌های انبار: {str(e)}")

    return redirect('invoice_list')  # تغییر به نام URL واقعی شما