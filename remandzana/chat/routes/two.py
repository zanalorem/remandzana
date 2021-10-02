from ..lobbies import ALL_LOBBIES
from ..utils import chat
from ...models.role import Role


async def two():
    return await chat(
        ALL_LOBBIES["two"],
        role=Role.NONE,
        first_navbar_link={
            "route": "chat.two",
            "text": "New conversation"
        }
    )
