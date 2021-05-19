from enum import Enum, auto


class Pieces(Enum):
    Pawn = auto(),
    Rook = auto(),
    Knight = auto(),
    Bishop = auto(),
    Queen = auto(),
    King = auto()


class Colors(Enum):
    Black = auto(),
    White = auto()
