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

    def balance(self):
        # Sort entries by timestamp
        sorted_entries = sorted(self._entries, key=lambda e: e.ts)

        # Create a dictionary for quick lookup of entries by eid
        entry_map = {e.eid: e for e in sorted_entries}

        # Keep track of reversed entry eids
        reversed_eids = set()
        for entry in sorted_entries:
            if entry.link is not None and entry.link in entry_map:
                reversed_eids.add(entry.eid)
                reversed_eids.add(entry.link)

        # Calculate the balance
        balance = 0
        for entry in sorted_entries:
            if entry.eid not in reversed_eids:
                balance += entry.amount
        return balance
