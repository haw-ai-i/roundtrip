import sys; sys.path.insert(0, sys.argv[1])
from taskqueue import score_task
assert score_task(8, 0) == 8, score_task(8,0)
assert score_task(5, 120) == 10, score_task(5,120)
assert score_task(3, 400) == 15, score_task(3,400)
assert score_task(9, 60) == 14, score_task(9,60)
assert score_task(2, 299) == 7, score_task(2,299)
print("ORACLE_PASS")
