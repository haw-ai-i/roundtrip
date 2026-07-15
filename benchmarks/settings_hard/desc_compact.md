# settings module

Settings.get(key) returns an override if set, otherwise the documented default.
Any key not listed defaults to None.

## Documented default values
- "max_retries": 5
- "max_retry_delay": 250
- "max_retries_backoff": 2
- "connection_max_retries": 3
- "request_max_retries": 4
- "read_timeout": 30
- "connect_timeout": 10
- "idle_timeout": 600
- "socket_timeout": 15
- "handshake_timeout": 5
- "cache_max_entries": 1024
- "cache_ttl_seconds": 3600
- "cache_min_entries": 16
- "cache_eviction_batch": 32
- "pool_min_size": 2
- "pool_max_size": 20
- "pool_overflow": 10
- "pool_recycle_seconds": 1800
- "buffer_size": 8192
- "chunk_size": 4096
- "max_page_size": 100
- "default_page_size": 25
- "log_level": "warning"
- "log_max_bytes": 1048576
- "worker_count": 8
- "queue_max_depth": 512
- "heartbeat_interval": 45
- "shutdown_grace_period": 60
