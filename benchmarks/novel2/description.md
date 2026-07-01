# policyengine module

Resolves access-control decisions from rules.

## Rule
priority (int, higher wins), effect ('allow'/'deny'), principal (name or '*'),
action (name or '*'). matches() is true when principal and action each equal the
request or are '*'.

## Decision contract (IMPORTANT - not enforced by is_allowed, which trusts input order)
A correct decision requires evaluating rules in this order:
1. Higher priority first.
2. At EQUAL priority, 'deny' is evaluated before 'allow' (deny-override).
3. First matching rule decides; 'allow'->True, 'deny'->False.
4. No match -> DENY (False).

is_allowed assumes the caller already sorted rules into this order. Any new
feature that resolves decisions must reproduce this ordering itself.
