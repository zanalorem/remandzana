import hmac
import json
import time
import base64
import binascii
from functools import wraps

from quart import current_app, abort, request, redirect

previous_auth = {"time": None}


def _gen_digest(data):
    return hmac.digest(get_secret_key(), data, "sha256")


def get_secret_key():
    secret_key = current_app.config["SECRET_KEY"]
    if not isinstance(secret_key, bytes):
        secret_key = secret_key.encode()
    return secret_key


def generate_signature(clavis, timestamp, role_setup, salt=None):
    data = [clavis, timestamp, role_setup]
    data = json.dumps(data).encode()
    return _gen_digest(data).hex()


def check_signature(signature, clavis, timestamp, role_setup, salt=None):
    genuine_signature = generate_signature(clavis, timestamp, role_setup)
    return hmac.compare_digest(genuine_signature, signature)


def requires_authentication(function):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        if not current_app.config.get("REMANDZANA_DEBUG"):
            return await abort(404)
        key = request.args.get("key")
        if check_authentication_key(key):
            return await function(*args, **kwargs)
        new_key = generate_authentication_key()
        if new_key is not None:
            print("New debug authentication key:", new_key)
        if key == "":
            return await abort(401)
        return redirect("?key=")
    return wrapper


def _gen_auth_key(time_string):
    time_bytes = time_string.encode()
    digest = _gen_digest(time_bytes)[:16]
    key = digest + time_bytes
    key = base64.urlsafe_b64encode(key).decode()
    return key


def generate_authentication_key():
    AUTH_COOLDOWN = current_app.config.get("REMANDZANA_AUTH_COOLDOWN", 10)

    # Don't generate new authentication keys too quickly.
    time_int = int(time.time())
    prev = previous_auth["time"]
    if prev is not None and time_int - prev < AUTH_COOLDOWN:
        return None
    else:
        previous_auth["time"] = time_int

    return _gen_auth_key(time_string=f"{time_int:x}")


def check_authentication_key(key):
    AUTH_TIMEOUT = current_app.config.get("REMANDZANA_AUTH_TIMEOUT", 600)

    # Key is not valid base64.
    try:
        key = base64.urlsafe_b64decode(key)
    except (TypeError, binascii.Error):
        return False

    digest, time_bytes = key[:16], key[16:]

    # Key is not genuine.
    genuine_digest = _gen_digest(time_bytes)[:16]
    if not hmac.compare_digest(genuine_digest, digest):
        return False

    # Key is too old.
    time_int = int(time_bytes.decode(), 16)
    if int(time.time()) - time_int >= AUTH_TIMEOUT:
        return False

    # Key is ok.
    previous_auth["time"] = time_int
    return True
