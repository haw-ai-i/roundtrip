class RetryPolicy:
    def __init__(self, base_delay, max_delay, max_attempts):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts

    def delay_for(self, attempt):
        return self.base_delay
