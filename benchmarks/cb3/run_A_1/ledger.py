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
        """
        Computes the balance of the ledger.

        The balance is computed by summing the amounts of all entries.
        If an entry has a link to another entry, its amount is added
        twice to the balance.
        """
        balance_val = 0
        for entry in self._entries:
            balance_val += entry.amount
            if entry.link is not None:
                balance_val += entry.amount
        return balance_val
