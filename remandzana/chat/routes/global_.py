from quart import current_app

from ..utils import chat
from ...models.role import Role


async def global_():
    return await chat(
        current_app.lobbies["global"],
        role=Role.NONE,
        first_navbar_link={
            "route": "chat.global_",
            "text": "Refresh"
        }
    )
