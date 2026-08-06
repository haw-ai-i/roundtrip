# Implementation target
Write the module at `django/utils/dateparse.py`.

## `django/utils/dateparse.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `date_re`
- `datetime_re`
- `iso8601_duration_re`
- `parse_date`
- `parse_datetime`
- `parse_duration`
- `parse_time`
- `postgres_interval_re`
- `standard_duration_re`
- `time_re`

Implement them to satisfy the specification. Do not write tests.
