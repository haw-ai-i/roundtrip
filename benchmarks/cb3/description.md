# ledger module

Computes an account balance from entries.

## Balance contract (total() is naive - sums all amounts in insertion order)
A correct balance must:
1. Process entries in TIMESTAMP (ts) order, ascending.
2. If an entry has `reverses` set to another entry's eid, that reversal CANCELS
   the referenced entry: neither the reversed entry nor the reversal contributes
   to the balance.
3. All other entries contribute their amount.
