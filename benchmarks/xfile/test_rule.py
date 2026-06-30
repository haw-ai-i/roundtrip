from minilib.accounts import Account
from minilib.registry import Registry

def test_hyphen_allowed_everywhere():
    a = Account("good-name")
    a.rename("another-name")
    r = Registry()
    assert r.register("reg-name")
    assert r.bulk_register(["a-b", "c-d"])
    print("PASS: hyphens accepted across all files")

test_hyphen_allowed_everywhere()
