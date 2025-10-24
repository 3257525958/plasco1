from django.urls import path
from . import views

app_name = 'pos_payment'

urlpatterns = [
    path('pos/', views.payment_page, name='payment_page'),
    path('pay/', views.send_amount_to_pos, name='send_payment'),
    path('test/', views.test_connection, name='test_connection'),
]