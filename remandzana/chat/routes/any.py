from quart import Markup

from ..lobbies import ALL_LOBBIES
from ..utils import chat
from ...models.role import Role

RANDOM_LOBBIES = [
    ALL_LOBBIES["two"],
    ALL_LOBBIES["three"],
    ALL_LOBBIES["question"]
]


async def custom_join_message(person):
    person.ignore_events.add("_on_lobby_join")
    await person.feed.put({"sender": None, "body": "Looking for people..."})


async def any_():
    return await chat(
        *RANDOM_LOBBIES,
        role=Role.NONE,
        after_person_init=custom_join_message,
        first_navbar_link={
            "route": "chat.any_",
            "text": Markup("New conversation<sup>*</sup>")
        }
    )
