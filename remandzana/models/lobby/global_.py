from quart import escape, Markup

from . import Lobby
from ..role import Role


class GlobalLobby(Lobby):
    MODE_NAME = "Global chat"
    _ROLES_REQUIRED = {Role.NONE: 1}
    _CLOSE_ROOM_UPON_CREATION = False
    _ROOM_COMMAND_PREFIX = "/"

    @staticmethod
    def room_appearance(person, viewer):
        color = person.extra.get("color", "var(--color-alice)")
        name = person.extra.get("name", "Anonymous")
        return Markup(
            f'<span class="name" style="color:{color};">'
            f"{escape(name)}"
            "</span>"
        )

    @staticmethod
    async def room_command(room, person, command):
        await person.feed.put({"sender": person, "body": command})
        key, *args = command.split()
        key = key.lower()
        if key == "/help":
            await person.feed.put({
                "sender": None,
                "body": "List of commands:\n"
                        " /ping  ping\n"
                        " /help  show this list of commands"
            })
        elif key == "/ping":
            await person.feed.put({
                "sender": None,
                "body": "Pong."
            })
        else:
            await person.feed.put({
                "sender": None,
                "body": "Command was not recognized. Type /help to see a list "
                        "of commands."
            })

    async def _on_lobby_join(self, person):
        pass

    async def _person_can_join_room(self, person, room):
        return True

    async def _on_room_join(self, room, person):
        messages = []
        if len(room.people) > 1:
            messages.append({
                "sender": None,
                "body": f"Welcome to the room. There are {len(room.people)} "
                        "people here (including you).",
                "event": "_on_room_join"
            })
        else:
            messages.append({
                "sender": None,
                "body": "Welcome to the room. You're the only one here "
                        "right now.",
                "event": "_on_room_join"
            })
        messages.append({
            "sender": None,
            "body": "Type /help to see a list of commands.",
            "event": "_on_room_join"
        })
        for message in messages:
            await person.feed.put(message)

        message = {
            "sender": None,
            "body": lambda viewer: Markup(
                f"&gt; {person.appearance_to(viewer)} joined."
            ),
            "event": "_on_room_join"
        }
        await room.broadcast(message, exclude=person)

    @staticmethod
    async def _on_room_exit(room, person):
        message = {
            "sender": None,
            "body": lambda viewer: Markup(
                f"&lt; {person.appearance_to(viewer)} left."
            ),
            "event": "_on_room_exit"
        }
        await room.broadcast(message)

        if len(room.people) == 0:
            for lobby in room.lobbies:
                try:
                    lobby._open_rooms.remove(room)
                except ValueError:
                    pass
