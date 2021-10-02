import time
from collections import OrderedDict


class Metrics:
    def __init__(self, metrics_period, metrics_cooldown):
        self.metrics_period = metrics_period
        self.metrics_cooldown = metrics_cooldown

        self._messages = OrderedDict()
        self._nb_messages = {"time": None, "nb": None}

    @property
    def messages(self):
        return self._messages.keys()

    def _discard_messages(self):
        """Discard records of old messages.
        """
        t = int(time.time())
        old = []
        for timestamp in self._messages:
            if t - timestamp >= self.metrics_period:
                old.append(timestamp)
            # This assumes that `self._messages` has sorted keys; if it doesn't
            # have sorted keys then `self.observe_messages` will return
            # incorrectly large values.
            else:
                break
        for timestamp in old:
            self._messages.pop(timestamp)

    def record_message(self, timestamp=None):
        """Record that a message was sent at a particular timestamp.
        """
        timestamp = timestamp or int(time.time())
        self._messages[timestamp] = self._messages.get(timestamp, 0) + 1
        self._discard_messages()

    def nb_messages(self):
        """Returns the number of messages sent during the last metrics
        period. If this calculation was done recently a cached result is
        returned instead.
        """
        t = int(time.time())
        prev = self._nb_messages["time"]
        if prev is not None and t - prev < self.metrics_cooldown:
            return self._nb_messages["nb"]
        else:
            self._discard_messages()
            nb = sum(self._messages.values())
            self._nb_messages["nb"] = nb
            self._nb_messages["time"] = t
        return nb
