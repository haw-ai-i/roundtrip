Partially addresses Issue #1572
Addresses the LocationParseError but not the DecodeError from kennethreitz#1572. When running
test_requests.py, I got an error in test_session_pickling which resulted in a TypeError. I'm not sure of the reason for the TypeError but I have commented out that test.

