from quart import Markup

from . import Lobby
from ...models.role import Role


class TwoLobby(Lobby):
    _ROLES_REQUIRED = {Role.NONE: 2}

    @staticmethod
    def room_appearance(person, viewer):
        if person is viewer:
            return Markup('<span class="name alice">You</span>')
        return Markup('<span class="name bob">Stranger</span>')

    async def _on_lobby_join(self, person):
        message = {
            "sender": None,
            "body": "Looking for a random...",
            "event": "_on_lobby_join"
        }
        await person.feed.put(message)

    async def _on_room_join(self, room, person):
        message = {
            "sender": None,
            "body": "Found someone. Say hi!",
            "event": "_on_room_join"
        }
        await person.feed.put(message)

    @staticmethod
    async def _on_room_exit(room, person):
        message = {
            "sender": None,
            "body": "The random left.",
            "event": "_on_room_exit"
        }
        await room.broadcast(message)

        if len(room.people) == 1:
            for person in room.people:
                person.abandon()
