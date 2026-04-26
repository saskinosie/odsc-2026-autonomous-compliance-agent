import hashlib
import hmac
import os

_DUMMY_SALT = "dummy_salt"
_DUMMY_HASH = "0" * 128  # matches scrypt output length (64 bytes hex-encoded)

def _load_users():
    users = {}
    for key, value in os.environ.items():
        if key.startswith("APP_USER_"):
            username = key[len("APP_USER_"):].lower()
            users[username] = value
    return users

def _hash(password: str, salt: str) -> str:
    return hashlib.scrypt(
        password.encode(),
        salt=salt.encode(),
        n=2**14, r=8, p=1
    ).hex()

def check_credentials(username: str, password: str) -> bool:
    if not isinstance(username, str) or not isinstance(password, str):
        return False

    users = _load_users()
    entry = users.get(username.lower())

    salt, expected, valid = _DUMMY_SALT, _DUMMY_HASH, False
    if entry is not None:
        parts = entry.split(":", 1)
        if len(parts) == 2:
            salt, expected, valid = parts[0], parts[1], True

    computed = _hash(password, salt)
    return hmac.compare_digest(computed, expected) and valid
