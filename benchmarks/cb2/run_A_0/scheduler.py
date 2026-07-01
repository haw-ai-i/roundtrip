class RetryPolicy:
    def __init__(self, base_delay, max_delay, max_attempts):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts

    def delay_for(self, attempt):
        return self.base_delay

    def schedule(self):
        delays = []
        for attempt in range(1, self.max_attempts + 1):
            delay = self.delay_for(attempt)
            # Apply the module's delay contract: delay should not exceed max_delay
            delays.append(min(delay, self.max_delay))
        return delays
