from reverse import reverse


def test_reverse_ascii():
    assert reverse("abc") == "cba"


def test_reverse_empty():
    assert reverse("") == ""
