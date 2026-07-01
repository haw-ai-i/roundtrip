import sys; sys.path.insert(0, sys.argv[1])
from policyengine import Rule, PolicyEngine
rules = [Rule(5,'allow','*','read'), Rule(10,'allow','alice','*'), Rule(10,'deny','alice','delete')]
e = PolicyEngine(rules)
d = e.resolve('alice','delete');  assert d is not None and d.effect=='deny' and d.priority==10, f"deny-override failed: {d}"
d2 = e.resolve('bob','read');     assert d2 is not None and d2.effect=='allow' and d2.priority==5, f"got {d2}"
d3 = e.resolve('bob','delete');   assert d3 is None, f"expected None, got {d3}"
print("ORACLE_PASS")
