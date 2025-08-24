from django.urls import path

from cantact_app import views

urlpatterns = [
    path('login/',views.logindef),
    path('logout/',views.logout_view),
    path('addcontact/',views.addcantactdef),
    path('ignor/',views.ignordef),
    path('addphon/',views.addphone),
    path('addreservecantact/',views.saveaccantdef),

    path('edit-profile/', views.edit_profile, name='edit_profile'),


]
