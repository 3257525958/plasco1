from django.urls import path
from . import views

app_name = 'sync_api'

urlpatterns = [
    path('push/', views.sync_push, name='sync_push'),
    path('pull/', views.sync_pull, name='sync_pull'),
]