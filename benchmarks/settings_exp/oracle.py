import sys; sys.path.insert(0, sys.argv[1])
from settings import Settings
s = Settings()
assert s.get("timeout") == 30, s.get("timeout")
assert s.get("retries") == 5, s.get("retries")
assert s.get("cache_size") == 256, s.get("cache_size")
assert s.get("log_level") == "warning", s.get("log_level")
assert s.get("batch_size") == 64, s.get("batch_size")
assert s.get("unknown") is None, s.get("unknown")
assert Settings({"timeout": 99}).get("timeout") == 99
print("ORACLE_PASS")
