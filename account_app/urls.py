

from django.urls import path
from . import views
# app_name = 'account_app'


urlpatterns = [
    path('inventory/', views.inventory_management, name='inventory_management'),


    path('get-branches/', views.get_branches, name='get_branches'),
    path('search-products/', views.search_products, name='search_products'),
    path('check-product/', views.check_product, name='check_product'),
    path('update-inventory-count/', views.UpdateInventoryCount.as_view(), name='update_inventory_count'),
    path('store-invoice-items/', views.StoreInvoiceItems.as_view(), name='store_invoice_items'),
    path('print-invoice/', views.print_invoice_view, name='print_invoice'),

    # path('admin/print-invoice/<int:invoice_id>/', admin_views.admin_print_invoice, name='admin_print_invoice'),

    path('get-branches/', views.get_branches, name='get_branches'),
    path('search-products/', views.search_products, name='search_products'),
    path('check-product/', views.check_product, name='check_product'),
    path('update-inventory-count/', views.UpdateInventoryCount.as_view(), name='update_inventory_count'),
    path('store-invoice-items/', views.StoreInvoiceItems.as_view(), name='store_invoice_items'),
    path('search_invoices/', views.search_invoices, name='search_invoices'),
    path('get_invoice_details/', views.get_invoice_details, name='get_invoice_details'),


# -----------------------مالی-------------------------------------------
path('invoice-status/<int:invoice_id>/', views.invoice_status, name='invoice_status'),


path('store-invoice-items/', views.StoreInvoiceItems.as_view(), name='store_invoice_items'),
# path('update-product-pricing/', views.UpdateProductPricing.as_view(), name='update_product_pricing'),

    path('search-branches-pricing/', views.search_branches_pricing, name='search_branches_pricing'),
    path('get-branch-products/', views.get_branch_products, name='get_branch_products'),
    # path('search-products-pricing/', views.search_products_pricing, name='search_products_pricing'),
    path('update-product-pricing/', views.update_product_pricing, name='update_product_pricing'),
    path('update-all-product-pricing/', views.update_all_product_pricing, name='update_all_product_pricing'),
    path('pricing-management/', views.pricing_management, name='pricing_management'),


# --------------------url-----------------------
    path('payment-methods/', views.payment_method_list, name='payment_method_list'),
    path('payment-methods/create/', views.payment_method_create, name='payment_method_create'),
    path('payment-methods/<int:pk>/update/', views.payment_method_update, name='payment_method_update'),
    path('payment-methods/<int:pk>/delete/', views.payment_method_delete, name='payment_method_delete'),
    path('payment-methods/<int:pk>/toggle-active/', views.payment_method_toggle_active,
         name='payment_method_toggle_active'),
    path('payment-methods/<int:pk>/set-default/', views.set_default_payment_method, name='set_default_payment_method'),
    path('check-auth/', views.check_auth_status, name='check_auth_status'),
    path('session-test/', views.session_test, name='session_test'),
]

