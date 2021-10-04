import secrets

from .utils import dump_feedback, load_feedbacks
from ..forms import Feedback
from ..auth import generate_signature

from quart import Blueprint, render_template, current_app, request, abort

bp = Blueprint("main", __name__)


@bp.route("/")
async def home():
    return await render_template(
        "home.html",
        nb_messages=current_app.metrics.nb_messages()
    )


@bp.get("/feedback")
async def view_feedback():
    salt = secrets.token_hex(16)
    signature = generate_signature(
        clavis=None,
        timestamp=None,
        role_setup=None,
        salt=salt
    )
    form = Feedback(
        salt=salt,
        signature=signature
    )
    return await render_template(
        "feedback.html",
        form=form,
        feedbacks=load_feedbacks(),
        nb_messages=current_app.metrics.nb_messages()
    )


@bp.post("/feedback")
async def submit_feedback():
    form = Feedback(await request.form)
    if form.validate():
        await dump_feedback(
            form.message.data,
            form.salt.data,
            form.signature.data
        )
        return await render_template("redirect.html")
    return await abort(403)


@bp.get("/about")
async def about():
    return await render_template(
        "about.html",
        lobbies=current_app.lobbies.values(),
        nb_messages=current_app.metrics.nb_messages()
    )
