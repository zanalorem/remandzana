from ..lobbies import ALL_LOBBIES
from ..utils import chat
from ...models.role import Role


async def global_():
    return await chat(
        ALL_LOBBIES["global"],
        role=Role.NONE,
        first_navbar_link={
            "route": "chat.global_",
            "text": "Refresh"
        }
    )
