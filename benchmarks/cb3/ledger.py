class Entry:
    def __init__(self, eid, amount, ts, link=None):
        self.eid = eid
        self.amount = amount
        self.ts = ts
        self.link = link

class Ledger:
    def __init__(self, entries):
        self._entries = list(entries)

    def total(self):
        return sum(e.amount for e in self._entries)
