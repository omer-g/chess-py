from enum import Enum, auto


class Pieces(Enum):
    Pawn = 1,
    Rook = auto(),
    Knight = auto(),
    Bishop = auto(),
    Queen = auto(),
    King = auto()


class Colors(Enum):
    Black = 1,
    White = auto()

    def other_color(self):
        return Colors.Black if self == Colors.White else Colors.White
