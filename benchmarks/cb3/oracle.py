import sys; sys.path.insert(0, sys.argv[1])
from ledger import Entry, Ledger
entries = [Entry('a',100,ts=1), Entry('b',50,ts=3), Entry('r',0,ts=2,link='a'), Entry('c',25,ts=4)]
L = Ledger(entries)
assert L.balance() == 75, f"got {L.balance()}"
print("ORACLE_PASS")
