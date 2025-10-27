# pos_payment/urls.py
from django.urls import path
from . import views

app_name = 'pos_payment'

urlpatterns = [
    path('', views.pos_payment_page, name='pos_payment'),
    path('check-connection/', views.check_connection, name='check_connection'),
    path('send-transaction/', views.send_transaction, name='send_transaction'),
]