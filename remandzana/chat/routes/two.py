from quart import current_app

from ..utils import chat
from ...models.role import Role


async def two():
    return await chat(
        current_app.lobbies["two"],
        role=Role.NONE,
        first_navbar_link={
            "route": "chat.two",
            "text": "New conversation"
        }
    )
