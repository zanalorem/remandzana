import abc
from collections import OrderedDict

from ..room import Room
from ...exceptions import PersonNotWanted


class Lobby(abc.ABC):
    MODE_NAME = NotImplemented
    _ROLES_REQUIRED = NotImplemented
    _CLOSE_ROOM_UPON_CREATION = True
    _ROOM_COMMAND_PREFIX = None

    def __init__(self, policies=()):
        self._people = OrderedDict()
        self._open_rooms = []
        self.policies = policies

    def __hash__(self):
        return hash(self.__class__.__name__)

    def json(self):
        return {
            "_ROLES_REQUIRED": {
                role.name: self._ROLES_REQUIRED[role]
                for role in self._ROLES_REQUIRED
            },
            "_CLOSE_ROOM_UPON_CREATION": self._CLOSE_ROOM_UPON_CREATION,
            "_ROOM_COMMAND_PREFIX": self._ROOM_COMMAND_PREFIX,
            "people": list(self._people),
            "_open_rooms": [room._locus for room in self._open_rooms]
        }

    @property
    def people(self):
        return self._people.values()

    @abc.abstractstaticmethod
    def room_appearance(person, viewer):
        raise NotImplementedError

    @staticmethod
    async def room_command(room, person, command):
        raise NotImplementedError

    @abc.abstractmethod
    async def _on_lobby_join(self, person):
        raise NotImplementedError

    async def _setup_role(self, person, text):
        raise NotImplementedError

    def _person_can_join_room(self, person, room):
        return False

    def _person_is_ready(self, person):
        return True

    async def _on_room_ready(self, room):
        if self._CLOSE_ROOM_UPON_CREATION:
            room.close()
        else:
            room._lobbies.add(self)
            self._open_rooms.append(room)

    @abc.abstractmethod
    async def _on_room_join(self, room, person):
        raise NotImplementedError

    @abc.abstractstaticmethod
    async def _on_room_exit(room, person):
        raise NotImplementedError

    async def add(self, person):
        """Add a person to the lobby. If the person is immediately admitted to
        a room returns the room and otherwise None.
        """
        if person.role not in self._ROLES_REQUIRED:
            raise PersonNotWanted(person, self)

        person._lobbies.append(self)
        self._people[person.clavis] = person
        await self._on_lobby_join(person)

        # try to choose an existing room
        room = await self._choose_room(person)
        if room is not None:
            return room

        # otherwise try to create a new room
        room = await self._create_room()
        if room is not None:
            return room

    def remove(self, person):
        person._lobbies.remove(self)
        self._people.pop(person.clavis)

    async def _choose_room(self, person, admit_person=True):
        """Tries to find a room stored in the cache (self._open_rooms) for the
        person to join. Returns the room if found and otherwise None.
        """
        for room in self._open_rooms:
            if await self._person_can_join_room(person, room):
                if admit_person:
                    self.remove(person)
                    room.admit(person)
                    await self._on_room_join(room, person)
                return room

    async def _create_room(self, admit_people=True):
        """Tries to create a room with the people in the lobby, prioritizing
        people who joined the lobby earlier. If no room could be created
        return None. Otherwise if `admit_people` is True admit the selected
        people to the room and return the room, and if `admit_people` is False
        return the list of selected people.
        """
        members = []
        roles = {}

        # for every person in the lobby who is ready
        for person in filter(self._person_is_ready, self.people):
            n = self._ROLES_REQUIRED.get(person.role, 0) \
                - roles.get(person.role, 0)
            # If this person has a required role that has not been exhausted
            # yet, add this person to the list.
            if n > 0:
                members.append(person)
                roles[person.role] = roles.get(person.role, 0) + 1
            # If we have the required number of people, break.
            if sum(roles.values()) == sum(self._ROLES_REQUIRED.values()):
                break
        else:
            # Couldn't create a room.
            return None

        # Create a room.
        room = Room(
            self.room_appearance,
            self.room_command,
            self._ROOM_COMMAND_PREFIX,
            self._on_room_exit,
            self.policies
        )
        if admit_people:
            # Admit everyone to the room.
            for person in members:
                self.remove(person)
                room.admit(person)
                await self._on_room_join(room, person)
            await self._on_room_ready(room)
            return room
        return members
