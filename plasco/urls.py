"""
URL configuration for plasco project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from home_app import views
from django.urls import path , include
from django.contrib import admin
from django.conf.urls.static import static
from . import settings
admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home_app.urls')),
    path('cantact/', include('cantact_app.urls')),
    path('dashbord/', include('dashbord_app.urls')),
    path('account/', include('account_app.urls')),

]
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
