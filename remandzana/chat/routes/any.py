from quart import current_app, Markup

from ..utils import chat
from ...models.role import Role


def lobbies():
    return (
        current_app.lobbies["two"],
        current_app.lobbies["three"],
        current_app.lobbies["question"]
    )


async def custom_join_message(person):
    person.ignore_events.add("_on_lobby_join")
    await person.feed.put({"sender": None, "body": "Looking for people..."})


async def any_():
    return await chat(
        *lobbies(),
        role=Role.NONE,
        after_person_init=custom_join_message,
        first_navbar_link={
            "route": "chat.any_",
            "text": Markup("New conversation<sup>*</sup>")
        }
    )
