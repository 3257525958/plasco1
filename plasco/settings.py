"""
Django settings for plasco project.
"""

from pathlib import Path
import os
import socket

BASE_DIR = Path(__file__).resolve().parent.parent

# تشخیص خودکار IP سرور
def get_server_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return None

SERVER_IP = get_server_ip()

# لیست IPهای مجاز برای حالت آفلاین
OFFLINE_ALLOWED_IPS = ['192.168.1.157', '127.0.0.1', 'localhost', '192.168.1.100', '192.168.1.101']
if SERVER_IP:
    OFFLINE_ALLOWED_IPS.append(SERVER_IP)

# تشخیص حالت اجرا
IS_OFFLINE_MODE = SERVER_IP in OFFLINE_ALLOWED_IPS if SERVER_IP else False

SECRET_KEY = 'django-insecure-9a=faq-)zl&%@!5(9t8!0r(ar)&()3l+hc#a)+-!eh$-ljkdh@'
DEBUG = True

if IS_OFFLINE_MODE:
    ALLOWED_HOSTS = OFFLINE_ALLOWED_IPS + ['plasmarket.ir', 'www.plasmarket.ir','192.168.1.172','192.168.1.157','localhost']
    # OFFLINE_ALLOWED_IPS = [
    #     '192.168.1.172',  # لپ‌تاپ تو
    #     '192.168.1.157',  # مودم
    #     # آی‌پی‌های دیگر دستگاه‌های شرکت رو اینجا اضافه کن
    #     '192.168.1.100',
    #     '192.168.1.101',
    #     '192.168.1.102',
    #     '127.0.0.1',
    #     'localhost'
    # ]
    print("حالت آفلاین - ديتابيس محلي")
else:
    ALLOWED_HOSTS = ['plasmarket.ir', 'www.plasmarket.ir', 'https://plasmarket.ir']
    CSRF_TRUSTED_ORIGINS = ["https://plasmarket.ir",'http://plasmarket.ir','https://www.plasmarket.ir','http://www.plasmarket.ir']
    print("حالت آنلاين - ديتابيس سرور")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',  # اختیاری - برای CORS
    'account_app.apps.AccountAppConfig',
    'dashbord_app.apps.DashbordAppConfig',
    'cantact_app.apps.CantactAppConfig',
    'invoice_app.apps.InvoiceAppConfig',
    'it_app.apps.ItAppConfig',
    'pos_payment.apps.PosPaymentConfig',
    'sync_app',
    'sync_api',
]
# تنظیمات REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

# تنظیمات CORS (اختیاری)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
JALALI_DATE_DEFAULTS = {
   'Strftime': {
        'date': '%y/%m/%d',
        'datetime': '%H:%M:%S _ %y/%m/%d',
    },
    'Static': {
        'js': [
            'admin/js/django_jalali.min.js',
        ],
        'css': {
            'all': [
                'admin/jquery.ui.datepicker.jalali/themes/base/jquery-ui.min.css',
            ]
        }
    },
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # باید اول باشد
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'plasco.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'plasco.wsgi.application'

if IS_OFFLINE_MODE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_offline.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'plascodavor_db',
            'USER': 'root',
            'PASSWORD': 'zh21oYmLXiINj!Es3Rtq',
            'HOST': 'plascodata1-ayh-service',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AZ_IRANIAN_BANK_GATEWAYS = {
   'GATEWAYS': {
       'IDPAY': {
           'MERCHANT_CODE': '021de8d3-3eb3-40ba-b0e3-01883a6575e1',
           'METHOD': 'POST',
           'X_SANDBOX': 1,
       },
   },
   'DEFAULT': 'IDPAY',
   'CURRENCY': 'IRR',
   'TRACKING_CODE_QUERY_PARAM': 'tc',
   'TRACKING_CODE_LENGTH': 16,
   'SETTING_VALUE_READER_CLASS': 'azbankgateways.readers.DefaultReader',
   'IS_SAFE_GET_GATEWAY_PAYMENT': True,
}

MERCHANT = '021de8d3-3eb3-40ba-b0e3-01883a6575e1'
SANDBOX = True

SYNC_INTERVAL = 600
ONLINE_SERVER_URL = "https://plasmarket.ir"
OFFLINE_MODE = IS_OFFLINE_MODE
ALLOWED_OFFLINE_IPS = OFFLINE_ALLOWED_IPS