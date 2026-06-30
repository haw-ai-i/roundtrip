"""Account creation and renaming (inline validation)."""

class Account:
    def __init__(self, username):
        if not (isinstance(username, str) and 3 <= len(username) <= 20
                and all(c.isalnum() or c == "_" for c in username)):
            raise ValueError("invalid username")
        self.username = username

    def rename(self, new_username):
        if not (isinstance(new_username, str) and 3 <= len(new_username) <= 20
                and all(c.isalnum() or c == "_" for c in new_username)):
            raise ValueError("invalid username")
        self.username = new_username
