# Remandzana

Random chat web application.

Uses long-lived HTTP requests, works without scripts or cookies.

Supported modes:
* two strangers
* three strangers
* question mode (à la Omegle)
* global chat

## Installation

Clone the repository.
```sh
git clone https://github.com/zanalorem/remandzana
cd remandzana
```

Install the requirements.
```sh
python -m pip install -r requirements.txt
```

Replace the secret key in `config.py`, for example with the result of `python -c "import secrets; print(secrets.token_hex(16))"`.

Quart comes with its own development server but for anything other than testing it's better to use a real [ASGI server](https://dev.to/bowmanjd/the-three-python-asgi-servers-5447).

### Etc.

By default a debug route `/debug` is exposed (can be disabled in `config.py`). Unauthenticated requests will print an authentication key to stdout.

Remandzana has a feedback form. Feedback is saved as JSON in the feedback folder (can be changed in `config.py`).
```json
{
    "timestamp": 1634000000,
    "datetime": "2021-10-12 00:53:20",
    "message": "message",
    "visible": false,
    "reply": null,
    "operator": false
}
```
`reply` should be null or a string. `operator` makes the message appear to be from the site operator.

## Contributing

Remandzana is new so contributions/issues/etc. are welcome.

## Documentation

Conversation logic is handled by three classes: [`Person`](/remandzana/models/person.py), [`Lobby`](/remandzana/models/lobby/__init__.py), and [`Room`](/remandzana/models/room.py). Lobbies are responsible for creating rooms and admitting people to rooms. The chat modes have one lobby class each (e.g. [`TwoLobby`](/remandzana/models/lobby/two.py) is the lobby for two-person mode). Lobbies are instantiated once in [lobbies.py](/remandzana/lobbies.py).

For example two-person mode works like this:
 * Somebody makes a GET request to `/two`. A new `Person` is added to the `TwoLobby`.
 * The lobby checks if it can create a new room. There is only one person in the lobby so it cannot.
 * Somebody else requests `/two`. Now there are two people in the lobby so it can create a new room.
 * The two people are admitted to the room and removed from the lobby.

This is the basic procedure for creating rooms. It works for the simple two-person and three-person modes but for anything more complicated (like question mode or global chat) it's not enough. The general procedure for creating rooms has a few more steps.

> `TwoLobby` and `ThreeLobby` forget about rooms as soon as they create them. This makes sense as you wouldn't expect a new person to be able to join an in-progress conversation in these modes. In global chat however, you would expect this because there is only one room. To allow for this lobbies can optionally keep track of what rooms they have created and try to admit new people to those rooms first before trying to create any new ones. (Only `GlobalLobby` does this.)

> Question mode requires three people, but one of them (the question author) isn't allowed to speak in the room, and before the room can be created they need to have submitted a question. This is accomplished using [roles](/remandzana/models/role.py). The question author has the `QUESTION` role which requires some setup to be done before the lobby will consider them _ready_.

Once a room exists, received messages are relayed to members of the room.

Sending a message is one request–response cycle and receiving the whole conversation log is one extremely long request–response cycle.
