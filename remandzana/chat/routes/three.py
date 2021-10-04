from quart import current_app, Markup

from ..utils import chat
from ...models.role import Role


async def three():
    return await chat(
        current_app.lobbies["three"],
        role=Role.NONE,
        first_navbar_link={
            "route": "chat.three",
            "text": Markup("New conversation<sup>3</sup>")
        }
    )
