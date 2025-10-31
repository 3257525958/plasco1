from django.urls import path
from . import views

app_name = 'sync_api'

urlpatterns = [
    path('pull/', views.sync_pull, name='sync_pull'),
    path('receive/', views.sync_receive, name='sync_receive'),
]