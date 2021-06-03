from enum import Enum, auto
from collections import namedtuple

INTRO = '''
        ##########################
        ######## chess-py ########
        ##########################

                    #
                   ###
                  ####
                 #### ##
                #### ####
                 ## ###
                  ####
               ##########
                  ####
                  ####
                  ####
                  ####
             ##############
             ##############
'''

# Starting position in FEN format
START_POSITION = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

# Board dimensions
DIM = 8
DIM_ZERO = 7

# Directions of movements
DIAGONAL = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
HORIZONTAL_VERTICAL = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ALL_DIRECTIONS = DIAGONAL + HORIZONTAL_VERTICAL
KNIGHT = [(1, 2), (-1, 2), (-1, -2), (1, -2), (2, 1), (-2, 1), (-2, -1), (2, -1)]

class BoardStatus(Enum):
    Normal = auto(),
    Check = auto(),
    Checkmate = auto(),
    Stalemate = auto()


class Colors(Enum):
    Black = 1,
    White = auto()

    def other_color(self):
        return Colors.Black if self == Colors.White else Colors.White
    
    def __str__(self):
        return "black" if self == Colors.Black else "white"

MoveReturn = namedtuple("MoveReturn", "status, promotion")

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
    def __init__(self, color, text, moves_counter = 0):
        self.color = color
        self.text = text
        self.moves_counter = moves_counter
        self.moves = set()
        self.threatens = set()
    
    def __str__(self):
        color = "w" if self.color == Colors.White else "b"
        return color + self.text

    __repr__ = __str__


class Pawn(Piece):
    def __init__(self, color, moves_counter = 0):
        super().__init__(color, "P", moves_counter = 0)

class Rook(Piece):
    def __init__(self, color, moves_counter = 0):
        super().__init__(color, "R", moves_counter = 0)
        self.can_castle = True

class Knight(Piece):
    def __init__(self, color, moves_counter = 0):
        super().__init__(color, "N", moves_counter = 0)

class Bishop(Piece):
    def __init__(self, color, moves_counter = 0):
        super().__init__(color, "B", moves_counter = 0)

class Queen(Piece):
    def __init__(self, color, moves_counter = 0):
        super().__init__(color, "Q", moves_counter = 0)

class King(Piece):
    def __init__(self, color, moves_counter = 0):
        super().__init__(color, "K", moves_counter = 0)
        self.can_castle = True


class Square:
    def __init__(self, coords: Coords):
        self.piece = None
        self.coords = coords

    def __str__(self):
        return self.piece.__str__() if self.piece else "  "
    
    __repr__ = __str__


class Record:
    def __init__(self, coords: Coords, piece):
        self.coords = coords
        self.piece_type = type(piece) if piece else None
        self.color = piece.color if piece else None
        self.moves_counter = piece.moves_counter if piece else None

    def __str__(self) -> str:
        return (" ".join(map(str, [self.coords,
                                   self.piece_type,
                                   self.color,
                                   self.moves_counter]))
        )
    
    __repr__ = __str__

if __name__=="__main__":
    print(Record(Coords(1,2), Pawn(Colors.Black)))
    print(Record(Coords(1,2), None))
