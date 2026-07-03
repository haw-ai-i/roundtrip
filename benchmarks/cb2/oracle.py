import sys; sys.path.insert(0, sys.argv[1])
from scheduler import RetryPolicy
p = RetryPolicy(base_delay=2, max_delay=20, max_attempts=6)
sched = p.schedule()
assert sched == [2, 4, 8, 16, 20, 20], f"got {sched}"
print("ORACLE_PASS")
