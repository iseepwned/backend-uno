from enum import Enum


class CardType(str, Enum):
    NUMBER = "NUMBER"
    TAKE_TWO = "TAKE_TWO"
    REVERSE = "REVERSE"
    JUMP = "JUMP"
    WILDCARD = "WILDCARD"
    TAKE_FOUR_WILDCARD = "TAKE_FOUR_WILDCARD"


class CardColor(str, Enum):
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    START = "EMPTY"
    WILDCARD = "WILDCARD"


class Direction(int, Enum):
    LEFT = -1
    RIGHT = 1
