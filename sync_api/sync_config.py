# sync_api/sync_config.py
SYNC_CONFIG = {
    'cantact_app': {
        'Branch': {
            'fields': ['name', 'address', 'phone', 'is_active', 'created_at'],
            'batch_size': 100,
            'sync_priority': 'high'
        },
        'BranchAdmin': {
            'fields': ['branch', 'user', 'role', 'is_active'],
            'batch_size': 100,
            'sync_priority': 'high'
        },
        'accuntmodel': {
            'fields': ['name', 'phone', 'email', 'address'],
            'batch_size': 100,
            'sync_priority': 'medium'
        },
        'dataacont': {
            'fields': ['name', 'phone', 'email'],
            'batch_size': 100,
            'sync_priority': 'medium'
        },
        'phonnambermodel': {
            'fields': ['number', 'type', 'is_active'],
            'batch_size': 100,
            'sync_priority': 'medium'
        },
        'savecodphon': {
            'fields': ['code', 'phone', 'is_used'],
            'batch_size': 100,
            'sync_priority': 'low'
        }
    }
}