from collections import OrderedDict

from ...exceptions import CensorshipPolicyViolation
from ...exceptions import CensorshipKick, CensorshipExile


class Policy:
    POLICY_NAME = NotImplemented
    REASON = NotImplemented
    SUPRESSED = "Your message was supressed."
    KICKED = "You have been kicked."
    EXILED = "You have been exiled site-wide."

    def __init__(self):
        self._consequences = OrderedDict()

    def _supress_notice(self, terse=SUPRESSED, verbose=SUPRESSED, index=0):
        notice = (index == 0) and verbose or terse
        if self._consequences["supress"] - index == 1:
            if "kick" in self._consequences:
                return f"{notice} You will be kicked next time."
            if "exile" in self._consequences:
                return f"{notice} You will be exiled next time."
        return notice

    def _kick_notice(self, index):
        return self.KICKED

    def _exile_notice(self, index):
        return self.EXILED

    def supress(self, nb_times):
        assert "supress" not in self._consequences
        assert "kick" not in self._consequences
        assert "exile" not in self._consequences
        self._consequences["supress"] = nb_times
        return self

    def kick(self):
        assert "kick" not in self._consequences
        assert "exile" not in self._consequences
        self._consequences["kick"] = 1
        return self

    def exile(self):
        assert "kick" not in self._consequences
        assert "exile" not in self._consequences
        self._consequences["exile"] = 1
        return self

    def consequence_after(self, nb_violations):
        i = 0
        for consequence in self._consequences:
            nb_times = self._consequences[consequence]
            if nb_violations - 1 in range(i, i + nb_times):
                index = (nb_violations - 1) - i
                return lambda policy, person: functions[consequence](
                    policy, person, index
                )
            i += nb_times
        return lambda policy, person: None


async def supress(policy, person, index=0):
    message = {"sender": None, "body": policy._supress_notice(index)}
    await person.feed.put(message)
    raise CensorshipPolicyViolation(person)


async def kick(policy, person, index=0):
    message = {"sender": None, "body": policy._kick_notice(index)}
    await person.feed.put(message)
    await person.room.kick(person)
    person.abandon()
    raise CensorshipKick(person)


async def exile(policy, person, index=0):
    message = {"sender": None, "body": policy._exile_notice(index)}
    await person.feed.put(message)
    await person.room.kick(person)
    person.abandon()
    raise CensorshipExile(person)

functions = {
    "supress": supress,
    "kick": kick,
    "exile": exile
}
