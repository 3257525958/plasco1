# pos_payment/urls.py
from django.urls import path
from . import views

app_name = 'pos_payment'

urlpatterns = [
    # صفحه اصلی
    path('pos/', views.pos_dashboard, name='dashboard'),

    # API‌ها
    path('get-network-info/', views.get_network_info_api, name='get_network_info'),
    path('test-connection/', views.test_connection, name='test_connection'),
    path('make-payment/', views.make_payment, name='make_payment'),
    path('clear-transactions/', views.clear_transactions, name='clear_transactions'),

    # صفحات
    path('history/', views.transaction_history, name='history'),
    path('transaction/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('guide/', views.pos_guide, name='guide'),
    path('settings/', views.pos_settings, name='settings'),
]