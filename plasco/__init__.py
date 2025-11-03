# plasco/__init__.py
# --------------------آفففلایت-----------------------------------------
# import threading
#
# def start_sync_service():
#     """شروع سرویس سینک در background"""
#     try:
#         from .sync_service import sync_service
#         print("🔄 راه‌اندازی سرویس سینک خودکار...")
#         sync_service.start_auto_sync()
#         print("✅ سرویس سینک خودکار فعال شد")
#     except Exception as e:
#         print(f"⚠️ خطا در شروع سرویس سینک: {e}")
#
# # شروع سرویس با تاخیر برای اطمینان از لود کامل جنگو
# def delayed_start():
#     import time
#     time.sleep(5)  # تاخیر 5 ثانیه
#     start_sync_service()
#
# # شروع سرویس در thread جداگانه
# try:
#     sync_thread = threading.Thread(target=delayed_start, daemon=True)
#     sync_thread.start()
# except Exception as e:
#     print(f"⚠️ خطا در شروع سرویس سینک: {e}")
#



# ---------------------آنلاین-----------------------------------------------------------

# import os
# import threading
#
#
# def start_sync_service():
#     """شروع سرویس سینک در background - فقط در حالت آفلاین"""
#     try:
#         # import داخل تابع برای جلوگیری از circular imports
#         from django.conf import settings
#
#         if getattr(settings, 'OFFLINE_MODE', False):
#             from .sync_service import sync_service
#             print("🔄 راه‌اندازی سرویس سینک خودکار در حالت آفلاین...")
#             sync_service.start_auto_sync()
#             print("✅ سرویس سینک خودکار فعال شد")
#         else:
#             print("🔵 سرور اصلی - سرویس سینک خودکار غیرفعال")
#
#     except Exception as e:
#         print(f"⚠️ خطا در شروع سرویس سینک: {e}")
#
#
# # بررسی حالت و شروع سرویس فقط در حالت آفلاین
# try:
#     # استفاده از environment variable برای تشخیص حالت
#     if os.environ.get('DJANGO_SETTINGS_MODULE') == 'plasco.settings':
#         from django.conf import settings
#
#         if getattr(settings, 'OFFLINE_MODE', False):
#             # فقط در حالت آفلاین و با تاخیر شروع شود
#             def delayed_start():
#                 import time
#                 time.sleep(10)  # تاخیر بیشتر برای اطمینان از لود کامل
#                 start_sync_service()
#
#
#             sync_thread = threading.Thread(target=delayed_start, daemon=True)
#             sync_thread.start()
#         else:
#             print("🔵 سرور اصلی - سرویس سینک غیرفعال (حالت آنلاین)")
# except Exception as e:
#     print(f"⚠️ خطا در بررسی وضعیت سینک: {e}")
