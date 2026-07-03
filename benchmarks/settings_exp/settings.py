class Settings:
    def __init__(self, overrides=None):
        self._overrides = overrides or {}

    def get(self, key):
        if key in self._overrides:
            return self._overrides[key]
        return self._default(key)

    def _default(self, key):
        raise NotImplementedError
