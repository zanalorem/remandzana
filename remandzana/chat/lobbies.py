from ..models.lobby.two import TwoLobby
from ..models.lobby.three import ThreeLobby
from ..models.lobby.question import QuestionLobby
from ..models.lobby.global_ import GlobalLobby

ALL_LOBBIES = {
    "two": TwoLobby(),
    "three": ThreeLobby(),
    "question": QuestionLobby(),
    "global": GlobalLobby()
}
