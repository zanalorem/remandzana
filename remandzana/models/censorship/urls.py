import re

from . import Policy


class URLs(Policy):
    POLICY_NAME = "Block URLs"
    REASON = "contained URL"

    def _check(self, message):
        matches = re.finditer(
            r'https?://(\w+\.)+\w+|([a-z2-7]{56}|[a-z2-7]{16})\.onion\S*',
            message,
            re.IGNORECASE
        )
        return any(matches)

    def _supress_notice(self, index):
        return super()._supress_notice(
            terse=f"Message suppressed ({self.REASON}).",
            verbose=(
                "Your message was supressed because URLs aren't allowed in "
                "this room."
            ),
            index=index
        )
