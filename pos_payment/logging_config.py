import logging
import os
from django.conf import settings


def setup_pos_logging():
    """تنظیمات لاگ‌گیری برای ماژول پوز"""

    # ایجاد دایرکتوری لاگ اگر وجود ندارد
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # فرمت لاگ
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # هندلر فایل
    file_handler = logging.FileHandler(
        os.path.join(log_dir, 'pos_payment.log'),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # هندلر کنسول
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # اعمال به logger ماژول
    pos_logger = logging.getLogger('pos_payment')
    pos_logger.setLevel(logging.DEBUG)
    pos_logger.addHandler(file_handler)
    pos_logger.addHandler(console_handler)

    return pos_logger