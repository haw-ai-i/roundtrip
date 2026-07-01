# scheduler module

RetryPolicy computes backoff delays between retry attempts.

## Delay contract (delay_for currently returns a flat base_delay - INCOMPLETE)
The correct delay for attempt n (1-based) is EXPONENTIAL:
  delay = base_delay * (2 ** (n - 1))
capped at max_delay (never exceed it). Attempt 1 uses base_delay.
Any feature computing a schedule must apply this exponential-with-cap rule.
