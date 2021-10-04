import operator

from quart import current_app, render_template, request, abort, make_response

from ..utils import make_form, handle_role_setup
from ...models.person import Person
from ...forms import Send
from ...auth import requires_authentication
from ...exceptions import CensorshipPolicyViolation
from ...exceptions import CensorshipKick, CensorshipExile


async def send():
    form = Send(await request.form)
    if form.validate():
        person = form.clavis.person
        body = form.message.data

        # request from a silenced person
        if person.silenced:
            return await abort(403)

        # setup message, e.g. submitting a question
        if form.setup.data:
            return await handle_role_setup(person, form.message.data)

        # room command
        elif person.room and person.room.is_command(body):
            await person.room.command(person.room, person, body)
            return await render_template(
                "send.html",
                form=make_form(person)
            )

        # regular chat message, person not in a room
        elif person.room is None:
            await person.warn()
            return await render_template(
                "send.html",
                form=make_form(person),
                value=body
            )

        # regular chat message
        else:
            message = {"sender": person, "body": body}
            try:
                await person.room.apply_censorship_policies(person, body)
            except CensorshipExile:
                response = await render_template(
                    "notalk.html",
                    placeholder="The chat has ended."
                ), 403
                response = await make_response(response)
                response.set_cookie("exiled", "true")
                return response
            except CensorshipKick:
                return await render_template(
                    "notalk.html",
                    placeholder="The chat has ended."
                ), 403
            except CensorshipPolicyViolation:
                if person.silenced:
                    return await render_template(
                        "notalk.html",
                        placeholder="The chat has ended."
                    ), 403
                return await render_template(
                    "send.html",
                    form=make_form(person),
                    value=body
                )
            await person.room.broadcast(message)
            current_app.metrics.record_message()
            return await render_template(
                "send.html",
                form=make_form(person)
            )

    if "signature" in form.errors or "timestamp" in form.errors:
        return await abort(403)
    if "message" in form.errors:
        return await abort(413)

    print("Form failed to validate:", form.errors)
    return await render_template(
        "notalk.html",
        placeholder="The chat has ended."
    ), 403


@requires_authentication
async def panopticon():
    import json

    response = json.dumps(
        {
            "people": Person._ALL_PEOPLE,
            "lobbies": {
                lobby.__class__.__name__: lobby
                for lobby in current_app.lobbies.values()
            },
            "rooms": {
                person.room._locus: person.room
                for person in Person._ALL_PEOPLE.values()
                if person.room
            }
        },
        default=operator.methodcaller("json")
    )
    return response, {"Content-Type": "application/json"}


routes = [
    {
        "rule": "/send",
        "view_func": send,
        "methods": ["POST"]
    },
    {
        "rule": "/debug",
        "view_func": panopticon
    }
]
