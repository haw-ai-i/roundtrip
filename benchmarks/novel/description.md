# policyengine module

Resolves access-control decisions from a set of rules.

## Rule
A Rule has: priority (int, higher evaluated first), effect ('allow' or 'deny'),
principal (a name or '*' wildcard), action (a name or '*' wildcard).
A rule matches a request when its principal and action each equal the request's
value or are '*'.

## PolicyEngine.is_allowed(principal, action) — decision contract
Rules are evaluated in a specific order and the FIRST matching rule decides:
1. Higher priority rules are evaluated before lower priority ones.
2. Within the SAME priority, a 'deny' rule is evaluated before an 'allow' rule
   (deny-override): if both a deny and an allow match at the same priority, deny wins.
3. The first matching rule's effect is returned ('allow' -> True, 'deny' -> False).
4. If NO rule matches, the default decision is DENY (return False).
