import re
from functools import lru_cache
from hashlib import md5

from quart import current_app

from . import Policy


@lru_cache(maxsize=1)
def blacklist():
    digests = set()
    with open(current_app.config["REMANDZANA_AHMIA_LOCATION"]) as fp:
        line = fp.readline().strip()
        if line:
            digests.add(bytes.fromhex(line))
    return digests


class Ahmia(Policy):
    POLICY_NAME = "Ahmia blacklist"
    REASON = "blacklisted URL"

    def _check(self, message):
        matches = re.finditer(
            r"[a-z2-7]{56}|[a-z2-7]{16}",
            message,
            re.IGNORECASE
        )
        for match in matches:
            onion = match.group().lower()
            digest = md5(f'{onion}.onion'.encode()).digest()
            if digest in blacklist():
                return True
        return False

    def _supress_notice(self, index):
        return super()._supress_notice(
            terse=f"Message suppressed ({self.REASON}).",
            verbose=(
                "Your message was supressed because it contained a "
                "blacklisted URL."
            ),
            index=index
        )
