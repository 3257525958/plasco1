# sync_app/management/commands/sync_config.py
SYNC_SETTINGS = {
    'enabled_models': [
        'account_app.Product',
        'account_app.Customer',
        'account_app.Expense',
        'invoice_app.Invoicefrosh',
        'invoice_app.InvoiceItemfrosh',
        # ... سایر مدل‌ها
    ],
    'sync_intervals': {
        'quick': 300,  # 5 دقیقه برای داده‌های مهم
        'normal': 600,  # 10 دقیقه
        'slow': 1800,   # 30 دقیقه برای داده‌های کم اهمیت
    },
    'retry_policy': {
        'max_retries': 3,
        'backoff_factor': 2,  # تصاعدی
    }
}