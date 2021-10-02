import time
import random
import secrets

from quart import render_template, make_response, current_app

from ..models.person import Person
from ..models.role import Role
from ..forms import Send
from ..auth import generate_signature


async def handle_role_setup(person, text):
    """Take input from the person necessary for setting up their role, for
    example submitting a question in question mode. This can be extended to
    allow for many-step role setups.
    """
    # It doesn't make much sense right now for someone to be in multiple
    # lobbies while a role setup is happening. The use of `.lobby` here
    # asserts that the person is in exactly 1 lobby.
    placeholder = await person.lobby._setup_role(person, text)
    person.silenced = True
    return await render_template("notalk.html", placeholder=placeholder)


def make_form(person, role_setup=False):
    timestamp = int(time.time())
    salt = secrets.token_hex(16)
    signature = generate_signature(
        person.clavis,
        timestamp,
        role_setup,
        salt
    )
    return Send(
        clavis=person.clavis,
        timestamp=timestamp,
        setup=role_setup,
        salt=salt,
        signature=signature
    )


async def chat(*lobbies, role=None, role_setup=False,
               form_placeholder="", after_person_init=None,
               first_navbar_link=None, second_navbar_link=None):
    person = Person(role=role or Role.NONE)
    if after_person_init is not None:
        await after_person_init(person)

    # Add person to lobbies.
    lobbies = list(lobbies)
    random.SystemRandom().shuffle(lobbies)
    for lobby in lobbies:
        await lobby.add(person)

    form_srcdoc = await render_template(
        "send.html",
        form=make_form(person, role_setup=role_setup),
        placeholder=form_placeholder,
        # "style-src 'self'" is broken in Firefox for iframes using srcdoc;
        # using a nonce instead is a workaround. Additionally Firefox has a
        # problem with caching srcdoc iframes, and it happens that if Firefox
        # decides to use a cached srcdoc, CSP is broken inside the iframe and
        # the iframe's stylesheet is blocked by the parent document's CSP
        # somehow. Importantly this means that it's possible to detect when
        # the iframe's srcdoc has come from a cache and show a warning.
        nonce=secrets.token_urlsafe(16)
    )
    preamble = await render_template(
        "chat.html",
        srcdoc=form_srcdoc,
        first_navbar_link=first_navbar_link,
        second_navbar_link=second_navbar_link,
        open_feedback_in_new_tab=True,
        hide_footer_about_link=True,
        nb_messages=current_app.metrics.nb_messages()
    )
    response = await make_response(person.readlines(preamble=preamble))
    response.timeout = None
    return response
