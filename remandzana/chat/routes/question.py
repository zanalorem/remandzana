import secrets

from quart import redirect, url_for

from ..lobbies import ALL_LOBBIES
from ..utils import chat
from ...models.role import Role


q_lobby = ALL_LOBBIES["question"]


async def question():
    if secrets.randbelow(3) == 0:
        return redirect(url_for(".question_discuss"))
    return redirect(url_for(".question_ask"))


async def question_discuss():
    return await chat(
        q_lobby,
        role=Role.NONE,
        first_navbar_link={
            "route": "chat.question_discuss",
            "text": "Discuss a question"
        },
        second_navbar_link={
            "route": "chat.question_ask",
            "text": "Ask a question"
        }
    )


async def question_ask():
    return await chat(
        q_lobby,
        role=Role.QUESTION,
        role_setup=True,
        form_placeholder="Ask a question...",
        first_navbar_link={
            "route": "chat.question_discuss",
            "mobile": "Discuss",
            "desktop": "Discuss a question"
        },
        second_navbar_link={
            "route": "chat.question_ask",
            "mobile": "Ask",
            "desktop": "Ask a question"
        }
    )
