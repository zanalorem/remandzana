import secrets
from collections import OrderedDict

from .role import Role
from .person import Person
from ..exceptions import RoomClosed


class Room:
    def __init__(self, appearance, command, command_prefix, on_exit):
        self._people = OrderedDict()
        self.appearance = appearance
        self.command = command
        self.command_prefix = command_prefix
        self.on_exit = on_exit
        self._closed = False
        self._lobbies = set()

        # extra information for lobbies to use and modify
        self.extra = {}

        # this room's unique identifier
        self._locus = secrets.token_hex(16)

    def json(self):
        return {
            "people": list(self._people.keys()),
            "command_prefix": self.command_prefix,
            "extra": self.extra,
            "_closed": self._closed,
            "locus": self._locus
        }

    def is_command(self, string):
        return self.command_prefix and string.startswith(self.command_prefix)

    @property
    def people(self):
        return self._people.values()

    @property
    def lobbies(self):
        return tuple(self._lobbies)

    def close(self):
        self._closed = True

    def admit(self, person):
        """Add a person to the room. Will raise PersonNotWanted if the
        person's role is not required.
        """
        if self._closed:
            raise RoomClosed(person, self)
        person.room = self
        person.index = sum(p.role == person.role for p in self.people)
        person.remove_from_lobbies()
        self._people[person.clavis] = person

    async def kick(self, person):
        """Remove a person from the room.
        """
        try:
            self._people.pop(person.clavis)
        except KeyError:
            pass
        await self.on_exit(self, person)

    async def broadcast(self, message, to=None, exclude=None):
        """Send a message to everyone in the room. If `to` is a Role, send only
        to people with that role. If `to` is a Person, send only to that
        person. If `exclude` is a Role, send to everyone without that Role. If
        `exclude` is a Person, send to everyone except that person.
        """
        if isinstance(to, Role):
            def match_to(person):
                return person.role == to
        elif isinstance(to, Person):
            def match_to(person):
                return person is to
        else:
            def match_to(person):
                return True

        if isinstance(exclude, Role):
            def match_exclude(person):
                return person.role == exclude
        elif isinstance(exclude, Person):
            def match_exclude(person):
                return person is exclude
        else:
            def match_exclude(person):
                return False

        def match(person):
            return match_to(person) and not match_exclude(person)

        for person in filter(match, self.people):
            await person.feed.put(message)
