
from django.urls import path
from . import views

app_name = 'invoice_app'

urlpatterns = [
    path('create/', views.create_invoice, name='create_invoice'),
    path('manage-pos-devices/', views.manage_pos_devices, name='manage_pos_devices'),
    path('search-product/', views.search_product, name='invoice_search_product'),
    path('add-item/', views.add_item_to_invoice, name='invoice_add_item'),
    path('remove-item/', views.remove_item_from_invoice, name='invoice_remove_item'),
    path('update-quantity/', views.update_item_quantity, name='update_item_quantity'),
    path('update-item-discount/', views.update_item_discount, name='update_item_discount'),
    path('save-customer-info/', views.save_customer_info, name='save_customer_info'),
    path('save-payment-method/', views.save_payment_method, name='save_payment_method'),
    path('save-pos-device/', views.save_pos_device, name='save_pos_device'),
    path('save-check-payment/', views.save_check_payment, name='save_check_payment'),
    path('save-credit-payment/', views.save_credit_payment, name='save_credit_payment'),
    path('save-discount/', views.save_discount, name='save_discount'),
    path('finalize/', views.finalize_invoice, name='finalize_invoice'),
    path('success/<int:invoice_id>/', views.invoice_success, name='invoice_success'),
    path('print/<int:invoice_id>/', views.invoice_print, name='invoice_print'),
    path('cancel/', views.cancel_invoice, name='invoice_cancel'),
    path('get-summary/', views.get_invoice_summary, name='get_invoice_summary'),
]
