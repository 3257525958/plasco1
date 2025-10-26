# pos_payment/urls.py
from django.urls import path
from . import views

app_name = 'pos_payment'

urlpatterns = [
    path('', views.pos_payment_page, name='pos_payment'),
    path('check-connection/', views.check_connection, name='check_connection'),
    path('send-transaction/', views.send_transaction, name='send_transaction'),
    path('test-api/', views.test_api, name='test_api'),
    path('test-simple-message/', views.test_simple_message, name='test_simple_message'),  # اضافه کردن این خط
    path('test-protocols/', views.test_protocols, name='test_protocols'),
]