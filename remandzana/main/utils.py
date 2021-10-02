import os
import base64
import json
import re
import time
from datetime import datetime

import aiofiles
from quart import current_app

from ..auth import check_signature


async def dump_feedback(message, salt, signature):
    feedback_dir = current_app.config["REMANDZANA_FEEDBACK_DIRECTORY"]
    os.makedirs(feedback_dir, exist_ok=True)

    salt = bytes.fromhex(salt)
    salt = base64.urlsafe_b64encode(salt).decode()

    signature = bytes.fromhex(signature)
    signature = base64.urlsafe_b64encode(signature).decode()

    t = int(time.time())
    feedback = {
        "timestamp": t,
        "datetime": datetime.utcfromtimestamp(t).strftime("%F %T"),
        "message": message,
        "visible": False,
        "reply": None,
        "operator": False
    }

    filename = f"{t}.{salt}.{signature}.json"
    filename = os.path.join(feedback_dir, filename)
    string = json.dumps(feedback, indent=4, ensure_ascii=False)
    async with aiofiles.open(filename, "w") as fp:
        await fp.write(string)


def _filename_is_ok(filename):
    match = re.fullmatch(
        r"[0-9]+\.([0-9a-zA-Z\-_]{22}==)\.([0-9a-zA-Z\-_=]{43}=)\.json",
        filename
    )
    if match is None:
        return False
    salt, signature = match.groups()
    salt = base64.urlsafe_b64decode(salt)[:16].hex()
    signature = base64.urlsafe_b64decode(signature)[:32].hex()
    return check_signature(
        signature=signature,
        timestamp=None,
        clavis=None,
        role_setup=None,
        salt=salt
    )


async def load_feedbacks():
    feedback_dir = current_app.config["REMANDZANA_FEEDBACK_DIRECTORY"]
    os.makedirs(feedback_dir, exist_ok=True)
    filenames = sorted(
        map(
            lambda filename: os.path.join(feedback_dir, filename),
            filter(_filename_is_ok, os.listdir(feedback_dir))
        ),
        reverse=True
    )
    for filename in filenames:
        async with aiofiles.open(filename) as fp:
            string = await fp.read(16384)
            if len(string) == 16384:
                print(f"Skipping extremely large feedback file: {filename}")
            yield json.loads(string)
