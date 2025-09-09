from django.urls import path
from . import views

urlpatterns = [
    path('inventory/', views.inventory_management, name='inventory_management'),
    # path('search-invoice/', views.search_invoice, name='search_invoice'),
    # path('update-inventory/', views.update_inventory, name='update_inventory'),
    # path('branch-inventory/<str:branch_id>/', views.get_branch_inventory, name='get_branch_inventory'),
    # path('product-inventory/<int:product_id>/', views.get_product_inventory, name='get_product_inventory'),
    # path('transfer-inventory/', views.transfer_inventory, name='transfer_inventory'),
    # path('search-products/', views.search_products, name='search_products'),


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
    path('search-invoices/', views.search_invoices, name='search_invoices'),
    path('get-invoice-details/', views.get_invoice_details, name='get_invoice_details'),
    path('store-invoice-items/', views.StoreInvoiceItems.as_view(), name='store_invoice_items'),





]