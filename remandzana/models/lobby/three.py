from quart import Markup, escape

from . import Lobby
from ...models.role import Role

APPEARANCE_DATA = [("Alice", "alice"), ("Bob", "bob"), ("Charlie", "charlie")]


class ThreeLobby(Lobby):
    _ROLES_REQUIRED = {Role.NONE: 3}

    @staticmethod
    def room_appearance(person, viewer):
        if person is viewer:
            suffix = ' <span class="you">(You)</span>'
        else:
            suffix = ""

        name, classname = APPEARANCE_DATA[person.index]
        return Markup(f'<span class="name {classname}">{name}</span>{suffix}')

    async def _on_lobby_join(self, person):
        message = {
            "sender": None,
            "body": "Looking for two randoms...",
            "event": "_on_lobby_join"
        }
        await person.feed.put(message)

    async def _on_room_join(self, room, person):
        message = {
            "sender": None,
            "body": "Found two people. Say hi!",
            "event": "_on_room_join"
        }
        await person.feed.put(message)

    @staticmethod
    async def _on_room_exit(room, person):
        name, classname = APPEARANCE_DATA[person.index]
        message = {
            "sender": None,
            "body": Markup(
                f'<span class="name {escape(classname)}">'
                f"{escape(name)}"
                "</span> left."
            ),
            "event": "_on_room_exit"
        }
        await room.broadcast(message)

        if len(room.people) == 1:
            for person in room.people:
                person.abandon()
