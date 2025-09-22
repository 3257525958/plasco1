from django.urls import path
from . import views

app_name = 'invoice_app'

urlpatterns = [
    path('create/', views.create_invoice, name='create_invoice'),
    path('search-product/', views.search_product, name='invoice_search_product'),
    path('add-item/', views.add_item_to_invoice, name='invoice_add_item'),
    path('remove-item/', views.remove_item_from_invoice, name='invoice_remove_item'),
    path('update-quantity/', views.update_item_quantity, name='update_item_quantity'),
    path('save-customer-info/', views.save_customer_info, name='save_customer_info'),
    path('save-payment-method/', views.save_payment_method, name='save_payment_method'),
    path('success/', views.invoice_success, name='invoice_success'),
    path('print/<int:invoice_id>/', views.invoice_print, name='invoice_print'),
    path('cancel/', views.cancel_invoice, name='invoice_cancel'),
]