from enum import Enum


class Role(Enum):
    NONE = 0
    QUESTION = 1

    def json(self):
        return self.name
