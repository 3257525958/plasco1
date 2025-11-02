# plasco/__init__.py
import threading

def start_sync_service():
    """شروع سرویس سینک در background"""
    try:
        from .sync_service import sync_service
        print("🔄 راه‌اندازی سرویس سینک خودکار...")
        sync_service.start_auto_sync()
        print("✅ سرویس سینک خودکار فعال شد")
    except Exception as e:
        print(f"⚠️ خطا در شروع سرویس سینک: {e}")

# شروع سرویس با تاخیر برای اطمینان از لود کامل جنگو
def delayed_start():
    import time
    time.sleep(5)  # تاخیر 5 ثانیه
    start_sync_service()

# شروع سرویس در thread جداگانه
try:
    sync_thread = threading.Thread(target=delayed_start, daemon=True)
    sync_thread.start()
except Exception as e:
    print(f"⚠️ خطا در شروع سرویس سینک: {e}")