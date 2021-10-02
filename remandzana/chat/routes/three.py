from quart import Markup

from ..lobbies import ALL_LOBBIES
from ..utils import chat
from ...models.role import Role


async def three():
    return await chat(
        ALL_LOBBIES["three"],
        role=Role.NONE,
        first_navbar_link={
            "route": "chat.three",
            "text": Markup("New conversation<sup>3</sup>")
        }

    )
