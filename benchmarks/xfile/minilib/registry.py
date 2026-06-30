"""Registry with inline username validation."""

class Registry:
    def __init__(self):
        self._names = set()

    def register(self, username):
        if not (isinstance(username, str) and 3 <= len(username) <= 20
                and all(c.isalnum() or c == "_" for c in username)):
            raise ValueError("cannot register invalid username")
        self._names.add(username)
        return True

    def bulk_register(self, names):
        for n in names:
            if not (isinstance(n, str) and 3 <= len(n) <= 20
                    and all(c.isalnum() or c == "_" for c in n)):
                raise ValueError(f"invalid in bulk: {n}")
            self._names.add(n)
        return len(self._names)
