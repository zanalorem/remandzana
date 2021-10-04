from .models.lobby.two import TwoLobby
from .models.lobby.three import ThreeLobby
from .models.lobby.question import QuestionLobby
from .models.lobby.global_ import GlobalLobby
from .models.censorship.ahmia import Ahmia
from .models.censorship.urls import URLs

two = TwoLobby(
    policies=[
        Ahmia().supress(5).kick()
    ]
)
three = ThreeLobby(
    policies=[
        Ahmia().supress(5).kick()
    ]
)
question = QuestionLobby(
    policies=[
        Ahmia().supress(5).kick()
    ]
)
global_ = GlobalLobby(
    policies=[
        Ahmia().supress(3).exile(),
        URLs().supress(5).kick()
    ]
)
ALL_LOBBIES = {
    "two": two,
    "three": three,
    "question": question,
    "global": global_
}
