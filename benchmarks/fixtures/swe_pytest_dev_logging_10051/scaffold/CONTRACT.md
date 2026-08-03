# Implementation target
Write the module at `src/_pytest/logging.py`.

## `src/_pytest/logging.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ColoredLevelFormatter`
- `DEFAULT_LOG_DATE_FORMAT`
- `DEFAULT_LOG_FORMAT`
- `LogCaptureFixture`
- `LogCaptureHandler`
- `LoggingPlugin`
- `PercentStyleMultiline`
- `caplog`
- `caplog_handler_key`
- `caplog_records_key`
- `catching_logs`
- `get_log_level_for_setting`
- `get_option_ini`
- `pytest_addoption`
- `pytest_configure`

Implement them to satisfy the specification. Do not write tests.
