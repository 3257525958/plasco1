# pos_payment/urls.py
from django.urls import path
from . import views

app_name = 'pos_payment'

urlpatterns = [
    path('', views.pos_payment_page, name='pos_payment'),
    path('check-connection/', views.check_connection, name='check_connection'),
    path('send-transaction/', views.send_transaction, name='send_transaction'),
    path('send-large-amount/', views.send_large_amount, name='send_large_amount'),
    path('send-200-billion/', views.send_200_billion, name='send_200_billion'),
    path('test-api/', views.test_api, name='test_api'),
    path('test-protocols/', views.test_protocols, name='test_protocols'),
    path('test-amounts/', views.test_amounts, name='test_amounts'),
]