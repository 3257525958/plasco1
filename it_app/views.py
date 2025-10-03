from django.shortcuts import render, redirect
from django.contrib import messages
from dashbord_app.models import Invoice, InvoiceItem

def invoice_list(request):
    """
    View to display the list of all invoices.
    """
    invoices = Invoice.objects.all().prefetch_related('items')
    return render(request, 'invoice_list.html', {'invoices': invoices})

def reset_remaining_quantity(request):
    """
    View to handle the reset action for selected invoices.
    """
    if request.method == 'POST':
        # Get the list of selected invoice IDs from the form
        selected_invoice_ids = request.POST.getlist('selected_invoices')

        if selected_invoice_ids:
            # Filter the InvoiceItems that belong to the selected invoices
            selected_items = InvoiceItem.objects.filter(invoice_id__in=selected_invoice_ids)

            # Update the remaining_quantity to equal the quantity for each item
            for item in selected_items:
                item.remaining_quantity = item.quantity
                # Use `update_fields` for efficiency if you are only changing this field
                item.save(update_fields=['remaining_quantity'])

            # Show a success message to the user
            messages.success(request, f'تعداد باقیمانده برای {len(selected_items)} آیتم با موفقیت بروزرسانی شد.')
        else:
            # Show a warning if no invoices were selected
            messages.warning(request, 'هیچ فاکتوری انتخاب نشده بود.')

    # Redirect back to the invoice list page
    return redirect('invoice_list')  # Make sure 'invoice_list' is the name of your URL pattern for the list view