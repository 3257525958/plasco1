

from django.urls import path
from . import views

urlpatterns = [
    path('sana/froshande/', views.froshande_view, name='froshande'),
    path('sana/froshande/<int:froshande_id>/accounts/', views.froshande_accounts_view, name='froshande_accounts'),
    path('sana/froshande/<int:froshande_id>/edit/', views.froshande_edit_view, name='froshande_edit'),
    path('sana/froshande/<int:froshande_id>/delete/', views.froshande_delete_view, name='froshande_delete'),
    path('sana/froshande/<int:froshande_id>/delete-ajax/', views.froshande_delete_ajax, name='froshande_delete_ajax'),
    path('sana/froshande/list/', views.froshande_list_view, name='froshande_list'),


    path('create-invoice/', views.create_invoice, name='create_invoice'),
    path('search-sellers/', views.search_sellers, name='search_sellers'),
    path('search-products/', views.search_products, name='search_products'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('confirm-invoice/', views.confirm_invoice, name='confirm_invoice'),

    path('search-invoices/', views.search_invoices, name='search_invoices'),
    path('edit-invoice/<int:invoice_id>/', views.edit_invoice, name='edit_invoice'),
    path('print-labels/<int:invoice_id>/', views.print_labels, name='print_labels'),


    # path('print-settings/', views.print_settings, name='print_settings'),
    # تغییر مسیر چاپ به پیش‌نمایش
    path('print-preview/<int:invoice_id>/', views.print_preview, name='print_preview'),
    # مسیر تنظیمات چاپ
    path('print-settings/', views.print_settings, name='print_settings'),



    path('usb/',views.usb_view, name='usb'),

]
