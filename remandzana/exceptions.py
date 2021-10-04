class PersonNotWanted(Exception):
    pass


class RoomClosed(Exception):
    pass


class PersonNotInLobby(Exception):
    pass


class CensorshipPolicyViolation(Exception):
    pass


class CensorshipKick(CensorshipPolicyViolation):
    pass


class CensorshipExile(CensorshipPolicyViolation):
    pass
