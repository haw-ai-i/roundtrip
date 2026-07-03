# settings module

Settings.get(key) returns an override if set, otherwise the default.

## Documented default values
- "timeout": 30
- "retries": 5
- "cache_size": 256
- "log_level": "warning"
- "batch_size": 64
Any key not listed defaults to None.
