from pychess import Bishop, Piece, Queen, Square
from PyQt5 import QtWidgets
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from enum import Enum, auto

DIM = 700
SQUARE_SIZE = 70
PIECE_SIZE = 60
DARK_COLOR = "grey"
BRIGHT_COLOR = "white"

class Pieces(Enum):
    Pawn = auto(),
    Rook = auto(),
    Knight = auto(),
    Bishop = auto(),
    Queen = auto(),
    King = auto(),
    Empty = auto()

class Colors(Enum):
    Black = auto(),
    White = auto()

PIECE_TO_PNG = {
    Pieces.Pawn: "pawn.png",
    Pieces.Rook: "rook.png",
    Pieces.Knight: "knight.png",
    Pieces.Bishop: "bishop.png",
    Pieces.Queen: "queen.png",
    Pieces.King: "king.png"
    }

COLOR_TO_PNG = {
        Colors.Black: "b_",
        Colors.White: "w_"
        }


# @param board_position: bottom left corner tuple (x, y)
# @param r, c: row and col  
class GuiSquare():
    def __init__(self, parent_window, board_position, r, c):
        piece = None
        self.x = board_position[0] + c * SQUARE_SIZE
        self.y = board_position[1] - r * SQUARE_SIZE
        square = QFrame(parent_window)
        square.setObjectName(u"frame" + f"{r}-{c}")
        square.setGeometry(QRect(self.x, self.y, SQUARE_SIZE, SQUARE_SIZE))
        if (r + c) % 2 == 0:
            square.setStyleSheet(f"background-color: {DARK_COLOR};")
        else:
            square.setStyleSheet(f"background-color: {BRIGHT_COLOR};")

    # @param parent_window: pass main window
    # @param piece: tuple of the enums Colors and Pieces
    # @param position: position of square (x, y)
    def place_piece(self, parent_window, piece_tuple):
        color, kind = piece_tuple

        self.piece = QtWidgets.QLabel(parent_window)
        self.piece.setPixmap(qtg.QPixmap(f"pieces/{COLOR_TO_PNG[color]}{PIECE_TO_PNG[kind]}"))
        self.piece.setGeometry(self.x + 5 , self.y + 5, PIECE_SIZE, PIECE_SIZE)
        self.piece.show()
                

class BoardWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(qtw.QGridLayout())
        self.resize(DIM,DIM)        
        self.setStyleSheet("BoardWindow {background-color: rgb(0,139,139);}") 
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.board_position = (DIM // 2 - SQUARE_SIZE * 4, DIM // 2 + SQUARE_SIZE * 3)
        
        # Draw board
        self.board = [[] for _ in range(0, 8)]
        for r, row in enumerate(self.board):
            for c in range(0, 8):
                row.append(GuiSquare(self, self.board_position, r, c))

        self.show()

    # This will accept a board state and set pieces accordingly.
    def set_pieces(self):
        for square in self.board[1]:
            square.place_piece(self, (Colors.White, Pieces.Pawn))
        for square in self.board[6]:
            square.place_piece(self, (Colors.Black, Pieces.Pawn))



app = qtw.QApplication([])
mw = BoardWindow()
mw.set_pieces()
app.exec_()


