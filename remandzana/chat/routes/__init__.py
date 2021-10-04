from quart import Blueprint

from ._common import routes as common_routes
from .two import two
from .three import three
from .question import question, question_ask, question_discuss
from .any import any_
from .global_ import global_
from ..utils import enforce_exile


bp = Blueprint("chat", __name__)


@bp.after_request
def cache_control(response):
    response.cache_control.no_store = True
    response.cache_control.max_age = 0
    return response


routes = [
    ("/two", two),
    ("/three", three),
    ("/question", question),
    ("/question/ask", question_ask),
    ("/question/discuss", question_discuss),
    ("/any", any_),
    ("/global", global_)
]

for r in common_routes:
    bp.add_url_rule(**r)

for rule, view_func in routes:
    bp.add_url_rule(rule=rule, view_func=enforce_exile(view_func))
