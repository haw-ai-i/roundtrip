class Rule:
    def __init__(self, priority, effect, principal, action):
        self.priority = priority
        self.effect = effect
        self.principal = principal
        self.action = action

    def matches(self, principal, action):
        return ((self.principal == '*' or self.principal == principal) and
                (self.action == '*' or self.action == action))


class PolicyEngine:
    def __init__(self, rules):
        self._rules = list(rules)

    def _ordered(self):
        return sorted(self._rules, key=lambda r: (-r.priority, 0 if r.effect == 'deny' else 1))

    def is_allowed(self, principal, action):
        for rule in self._ordered():
            if rule.matches(principal, action):
                return rule.effect == 'allow'
        return False
