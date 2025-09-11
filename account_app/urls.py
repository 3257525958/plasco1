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
    path('store-invoice-items/', views.StoreInvoiceItems.as_view(), name='store_invoice_items'),
    path('search_invoices/', views.search_invoices, name='search_invoices'),
    path('get_invoice_details/', views.get_invoice_details, name='get_invoice_details'),


# -----------------------مالی-------------------------------------------
path('invoice-status/<int:invoice_id>/', views.invoice_status, name='invoice_status'),


path('store-invoice-items/', views.StoreInvoiceItems.as_view(), name='store_invoice_items'),
path('update-product-pricing/', views.UpdateProductPricing.as_view(), name='update_product_pricing'),

    path('search-branches-pricing/', views.search_branches_pricing, name='search_branches_pricing'),
    path('get-branch-products/', views.get_branch_products, name='get_branch_products'),
    path('search-products-pricing/', views.search_products_pricing, name='search_products_pricing'),
    path('update-product-pricing/', views.update_product_pricing, name='update_product_pricing'),
    path('update-all-product-pricing/', views.update_all_product_pricing, name='update_all_product_pricing'),
    path('pricing-management/', views.pricing_management, name='pricing_management'),


]