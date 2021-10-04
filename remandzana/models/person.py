import asyncio
import secrets

from quart import escape, Markup

from .role import Role

HEARTBEAT = '\n<b><b><b></b></b></b>'


class Person:
    _ALL_PEOPLE = {}

    def __init__(self, role=None):
        # this person's unique identifier
        self._clavis = secrets.token_urlsafe(16)
        # this person's feed; messages go in and out of here
        self.feed = asyncio.Queue()

        self._role = role or Role.NONE
        self._index = None
        self._room = None
        self._lobbies = []

        # extra information for lobbies to use and modify
        self.extra = {}

        # If True, the person sent a message before they were placed in a room.
        self._warned = False
        # If True, all references to the person have already been deleted
        # (this is to ensure that self.readlines exits).
        self._deleted = False
        # If True, the person will be deleted as soon as their feed is empty.
        self._abandoned = False
        # censorship policy violations
        self._violations = {}

        # Ignore system messages caused by these events, e.g. "_on_lobby_join".
        self.ignore_events = set()
        # If True, future requests to /send will result in 403 Forbidden.
        self.silenced = False

        # internal clock; used to send heartbeat messages periodically
        self._clock = 0

        self._ALL_PEOPLE[self._clavis] = self

    def __repr__(self):
        return f"Person({self._clavis!r})"

    def json(self):
        return {
            "clavis": self.clavis,
            "role": self.role,
            "index": self.index,
            "room": self.room and self.room._locus,
            "lobbies": [lobby.__class__.__name__ for lobby in self.lobbies],
            "extra": self.extra,
            "_warned": self._warned,
            "_deleted": self._deleted,
            "_abandoned": self._abandoned,
            "ignore_events": list(self.ignore_events),
            "silenced": self.silenced
        }

    @property
    def clavis(self):
        return self._clavis

    @property
    def lobbies(self):
        return tuple(self._lobbies)

    @property
    def lobby(self):
        if len(self._lobbies) == 0:
            return None
        elif len(self._lobbies) == 1:
            return self._lobbies[0]
        assert False, (
            f"`lobby` attribute of {self!r} accessed when in "
            "{len(self.lobbies)} lobbies"
        )

    @property
    def role(self):
        return self._role

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, room):
        if self._room is not None:
            raise ValueError(
                f"Cannot change room from {self._room!r} (lobbies: "
                f"{self._room.lobbies}) to {room!r} (lobbies: "
                f"{room.lobbies}) for {self!r}")
        else:
            self._room = room

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        if self._index is not None:
            raise ValueError(f"Cannot change index for {self!r}")
        self._index = index

    def _tick(self):
        """Increment this person's clock. Returns True if the clock rolls over
        and False otherwise.
        """
        clock = self._clock
        self._clock = (clock + 1) % 12
        return clock == 0

    def appearance_to(self, viewer):
        if viewer is None:
            return ""
        return self.room.appearance(self, viewer)

    async def warn(self):
        """Called when this person tries to send a message before they've been
        admitted to a room.
        """
        if self._warned:
            return
        message = {"sender": None, "body": "You're not talking to anyone yet!"}
        await self.feed.put(message)
        self._warned = True

    def _formatline(self, message):
        """Returns a message rendered in HTML.
        """
        sender = message["sender"]
        body = message["body"]
        # allow body to be callable, for example to show different names
        if callable(body):
            body = body(self)
        # system messages have sender None
        if sender is None:
            rendered_sender = ""
            rendered_body = f'<div class="system">{escape(body)}</div>'
        else:
            rendered_sender = (
                '<span class="sender">'
                f"{escape(sender.appearance_to(self))}:"
                "</span> "
            )
            rendered_body = f'<bdi class="message">{escape(body)}</bdi>'
        line = f'\n<div class="line">{rendered_sender}{rendered_body}</div>'
        return Markup(line)

    async def readline(self):
        """Get a single message from the feed and return its rendered HTML.
        If there is no message, wait 0.5 seconds and return " " (or the
        heartbeat message). This is to be able to detect when clients
        disconnect; once the client has disconnected the attempt to send " "
        will raise asyncio.exceptions.CancelledError. Without the heartbeat
        message this would result in 7200 bytes of dummy traffic per hour per
        client (at most). With the heartbeat message this results in 19800
        bytes of extra traffic per hour per client (at most).

        It would be nice to be able to detect when a client disconnects
        in a way that doesn't involve constantly sending data. It might be
        possible but ASGI doesn't expose the state of the connection to the
        client so any solution would be specific to one webserver or ASGI
        server.
        """
        try:
            message = self.feed.get_nowait()
        except asyncio.QueueEmpty:
            await asyncio.sleep(0.5)
        else:
            if message.get("event") not in self.ignore_events:
                return self._formatline(message)
        return self._tick() and HEARTBEAT or " "

    async def readlines(self, preamble=None):
        """Yield all messages in the feed. If `preamble` is not None, yields
        `preamble` before anything else. If this person has been abandoned,
        calls `self.delete` once the feed is empty.
        """
        if preamble is not None:
            yield preamble
        while True:
            # If this person has already been deleted, return here to avoid
            # calling `self.delete` again.
            if self._deleted:
                return
            try:
                yield await self.readline()
            except asyncio.exceptions.CancelledError:
                await self.delete()
                raise
            if self._abandoned and self.feed.qsize() == 0:
                await self.delete()
                return

    async def please_refresh(self):
        """Prompt this person to refresh the page, then abandon this person.
        """
        message = {
            "sender": None,
            "body": "Something went wrong. Please refresh the page."
        }
        await self.feed.put(message)
        self.abandon()

    def abandon(self):
        """
        Abandon this person. When the feed is empty `self.readlines` will
        delete this person.
        """
        self._abandoned = True

    async def delete(self):
        """Deletes references to this person. References deleted are in
        `self.room` (if not None), `self.lobbies`, and `self._ALL_PEOPLE`.
        """
        self._deleted = True
        if self.room:
            await self.room.kick(self)
        try:
            self._ALL_PEOPLE.pop(self.clavis)
        except KeyError:
            pass
        self.remove_from_lobbies()

    def remove_from_lobbies(self):
        for lobby in self.lobbies:
            try:
                lobby.remove(self)
            except KeyError:
                pass

    def __del__(self):
        print("__del__", self)
