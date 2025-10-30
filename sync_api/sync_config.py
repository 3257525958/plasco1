# sync_api/sync_config.py
SYNC_CONFIG = {
    'account_app': {
        'Product': {
            'fields': ['name', 'description', 'price', 'category', 'stock_quantity', 'created_at', 'updated_at'],
            'batch_size': 100
        },
        'Customer': {
            'fields': ['name', 'phone', 'email', 'address', 'created_at'],
            'batch_size': 100
        }
    },
    'cantact_app': {
        'Contact': {
            'fields': ['name', 'phone', 'email', 'company', 'position', 'notes', 'created_at'],
            'batch_size': 100
        }
    },
    'invoice_app': {
        'Invoice': {
            'fields': ['invoice_number', 'customer_name', 'total_amount', 'date', 'status', 'created_at'],
            'batch_size': 50
        },
        'InvoiceItem': {
            'fields': ['invoice_id', 'product_name', 'quantity', 'unit_price', 'total_price'],
            'batch_size': 200
        }
    },
    'it_app': {
        'Device': {
            'fields': ['name', 'serial_number', 'type', 'status', 'assigned_to', 'created_at'],
            'batch_size': 50
        }
    },
    'pos_payment': {
        'Transaction': {
            'fields': ['transaction_id', 'amount', 'payment_method', 'status', 'created_at'],
            'batch_size': 100
        }
    }
}