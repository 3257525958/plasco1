from django.urls import path
from . import views

urlpatterns = [
    path('inventory/', views.inventory_management, name='inventory_management'),
    path('search-invoice/', views.search_invoice, name='search_invoice'),
    path('update-inventory/', views.update_inventory, name='update_inventory'),
    path('branch-inventory/<str:branch_id>/', views.get_branch_inventory, name='get_branch_inventory'),
    path('product-inventory/<int:product_id>/', views.get_product_inventory, name='get_product_inventory'),
    path('transfer-inventory/', views.transfer_inventory, name='transfer_inventory'),
    path('search-products/', views.search_products, name='search_products'),
]