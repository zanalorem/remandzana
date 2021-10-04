from quart import Markup, escape

from . import Lobby
from ...models.role import Role
from ...exceptions import PersonNotInLobby

APPEARANCE_DATA = [("Alice", "alice"), ("Bob", "bob")]


class QuestionLobby(Lobby):
    MODE_NAME = "Question mode"
    _ROLES_REQUIRED = {Role.NONE: 2, Role.QUESTION: 1}

    @staticmethod
    def room_appearance(person, viewer):
        if viewer.role == Role.QUESTION:
            name, classname = APPEARANCE_DATA[person.index]
            return Markup(f'<span class="name {classname}">{name}</span>')
        if person is viewer:
            return Markup('<span class="name alice">You</span>')
        return Markup('<span class="name bob">Stranger</span>')

    async def _on_lobby_join(self, person):
        if person.role == Role.QUESTION:
            message = {
                "sender": None,
                "body": "Waiting for your question...",
                "event": "_on_lobby_join"
            }
        else:
            message = {
                "sender": None,
                "body": "Looking for a question for you to discuss...",
                "event": "_on_lobby_join"
            }

        await person.feed.put(message)

    async def _setup_role(self, person, question):
        if person.clavis not in self._people:
            raise PersonNotInLobby(person, self)

        for policy in self.policies:
            if policy._check(question):
                message = {
                    "sender": None,
                    "body": f"Question rejected ({policy.REASON}).",
                    "event": "_setup_role"
                }
                await person.feed.put(message)
                return False, "Ask a question..."

        messages = [
            {
                "sender": None,
                "body": Markup(
                    "Your question is: "
                    f'<span class="question">{escape(question)}</span>'
                ),
                "event": "_setup_role"
            },
            {
                "sender": None,
                "body": "Looking for people to discuss your question...",
                "event": "_setup_role"
            }
        ]
        for message in messages:
            await person.feed.put(message)
        person.extra["question"] = question
        await self._create_room()

        return True, "Your question was submitted."

    def _person_is_ready(self, person):
        if person.role == Role.QUESTION:
            return "question" in person.extra
        return True

    async def _on_room_ready(self, room):
        question = room.extra.pop("question")
        message = {
            "sender": None,
            "body": Markup(
                "Found a question. Question: "
                f'<span class="question">{escape(question)}</span>'
            ),
            "event": "_on_room_ready"
        }
        await room.broadcast(message, to=Role.NONE)

    async def _on_room_join(self, room, person):
        if person.role == Role.QUESTION:
            room.extra["question"] = person.extra.pop("question")
            message = {
                "sender": None,
                "body": "Found two people. Watch them discuss your question!",
                "event": "_on_room_join"
            }
            await person.feed.put(message)

    @staticmethod
    async def _on_room_exit(room, person):
        if person.role == Role.QUESTION:
            message = {
                "sender": None,
                "body": "The OP left.",
                "event": "_on_room_exit"
            }
        else:
            message = {
                "sender": None,
                "body": lambda viewer: Markup(
                    f"{person.appearance_to(viewer)} left."
                ),
                "event": "_on_room_exit"
            }
        await room.broadcast(message)

        if len(room.people) == 1:
            for p in room.people:
                p.abandon()
