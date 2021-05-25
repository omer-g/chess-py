from enum import Enum, auto
from collections import namedtuple


# Board dimensions
DIM = 8
DIM_ZERO = 7

# Directions of movements
DIAGONAL = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
HORIZONTAL_VERTICAL = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ALL_DIRECTIONS = DIAGONAL + HORIZONTAL_VERTICAL
KNIGHT = [(1, 2), (-1, 2), (-1, -2), (1, -2), (2, 1), (-2, 1), (-2, -1), (2, -1)]


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


# Named tuple of coordinates
Coords = namedtuple("Coords", "r, c")


# Print Coords as regular tuples
def print_coords(self):
    t = tuple(self)
    return str(t)
Coords.__str__ = print_coords
Coords.__repr__ = Coords.__str__


# Check if coordinates on board
def on_board(coords):
    for coord in coords:
        if coord < 0 or coord > DIM_ZERO:
            return False
    return True


class Piece:
    def __init__(self, color, text):
        self.color = color
        self.text = text
        self.moves = set()
        self.threatens = set()
    
    def __str__(self):
        color = "w" if self.color == Colors.White else "b"
        return color + self.text

    __repr__ = __str__


class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, "P")

class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, "R")
        self.can_castle = True

class Knight(Piece):
    def __init__(self, color):
        super().__init__(color, "N")

class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color, "B")

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, "Q")

class King(Piece):
    def __init__(self, color):
        super().__init__(color, "K")
        self.can_castle = True


class Square:
    def __init__(self, coords: Coords):
        self.piece = None
        self.coords = coords

    def __str__(self):
        return self.piece.__str__() if self.piece else "  "
    
    __repr__ = __str__
