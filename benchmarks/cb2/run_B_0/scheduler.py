class RetryPolicy:
    def __init__(self, base_delay, max_delay, max_attempts):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts

    def delay_for(self, attempt):
        delay = self.base_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)

    def schedule(self):
        return [self.delay_for(attempt) for attempt in range(1, self.max_attempts + 1)]
