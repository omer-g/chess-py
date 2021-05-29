from chess import *

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
from functools import partial


# Size of window
WINDOW_DIM = 800

# Colors
DARK = "grey"
BRIGHT = "rgb(255, 253, 208)"
BG = "rgb(0,139,139)"

PIECE_PNG = {
    Pawn: "pawn.png",
    Rook: "rook.png",
    Knight: "knight.png",
    Bishop: "bishop.png",
    Queen: "queen.png",
    King: "king.png"
}

COLOR_PNG = {
        Colors.Black: "b_",
        Colors.White: "w_"
}


class BoardPiece(QtWidgets.QLabel):
    ''' A piece in the GUI '''
    def __init__(self, parent, color, kind):
        super().__init__()
        self.kind = kind
        self.color = color
        if color and kind:
            pix_map = QtGui.QPixmap("pieces/"
                                    f"{COLOR_PNG[color]}{PIECE_PNG[kind]}")
            self.setPixmap(pix_map.scaled(int(parent.width()*0.5),
                    int(parent.width()*0.5), QtCore.Qt.KeepAspectRatio))


class BoardSquare(QtWidgets.QFrame):
    ''' A square in the GUI '''
    def __init__(self, board_window, parent_widget, square_color, gui_coords):
        super().__init__(parent_widget)
        self.board_window = board_window
        self.board_widget = parent_widget
        self.gui_coords = gui_coords
        
        self.piece = None

        self.square_layout = QtWidgets.QVBoxLayout()
        self.square_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.setLayout(self.square_layout)
        self.setStyleSheet(f"background-color: {square_color};")
        self.setLineWidth(0)

    def place_piece(self, color, kind):
        self.remove_piece()
        piece = BoardPiece(self, color, kind)
        self.square_layout.addWidget(piece)
        self.piece = piece

    def remove_piece(self):
        if self.piece:
            self.square_layout.removeWidget(self.piece)
            self.piece = None
        
    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.board_window.handleDoubleClick(self)
        return super().mousePressEvent(a0)


class BoardWindow(QtWidgets.QWidget):
    ''' The game window '''

    # @param coords: a tuple of gui board coordinates
    # @return: coordinates on logic board as Coords.
    def gui_to_board_coords(self, coords):
        row, col = coords
        if self.white_perspective:
            return Coords(7 - row, col)
        else:
            return Coords(row, col)
    
    # @param square: a square in the gui
    # @return: coordinates on logic board as Coords.
    def square_to_board_coords(self, square):
        return self.gui_to_board_coords(square.gui_coords)

    # @param coords: a tuple of logic board coordinates
    # @return: coordinates on gui board.
    def board_to_gui_coords(self, coords):
        row, col = coords
        return tuple(self.gui_to_board_coords((row, col)))

    def call_promote(self, piece_type):
        self.board.promote_pawn(piece_type)
        self.set_pieces(self.board.get_state())
        
    def promote_dialog(self):
        promote_pieces = {
            Knight: "Knight",
            Bishop: "Bishop",
            Rook: "Rook",
            Queen: "Queen"
        }
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        dialog_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        dialog.setStyleSheet(f"QDialog {{background-color: {BG};}}")
        dialog.setLayout(dialog_layout)

        for piece_type in promote_pieces:
            button = QtWidgets.QPushButton(promote_pieces[piece_type], dialog)
            button.setStyleSheet("QPushButton {border: none};")
            button.setStyleSheet(f"QPushButton {{background-color: {BRIGHT};}}")
            button.isFlat = True

            button.clicked.connect(partial(self.call_promote, piece_type))
            button.clicked.connect(dialog.close)
            dialog_layout.addWidget(button)
        dialog.exec()

    # @param white_perspective: direction of board
    def __init__(self, white_perspective = True):
        super().__init__()

        # Marks if a piece is lifted and if so saves its square.
        self.piece_lifted = False
        self.origin_square = None
        self.white_perspective = white_perspective


        window_layout = QtWidgets.QGridLayout()
        self.setLayout(window_layout)
        self.resize(WINDOW_DIM,WINDOW_DIM)        
        self.setStyleSheet(f"BoardWindow {{background-color: {BG};}}")
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        
        self.board = Board()
        self.board_widget = QtWidgets.QFrame(self)
        self.board_squares = [[] for i in range(8)]
        board_layout = QtWidgets.QGridLayout()
        board_layout.setSpacing(0)
        self.board_widget.setLayout(board_layout)

        
        positions = [(i, j) for i in range(8) for j in range(8)]
        for i, j in positions:
            r, c = self.gui_to_board_coords((i, j))

            # Square color based on logic board coordinates
            square_color = DARK if (r + c) % 2 == 1 else BRIGHT
            square = BoardSquare(self, self.board_widget, square_color, (i, j))
            self.board_squares[i].append(square)
            board_layout.addWidget(square, i, j)
            
        window_layout.addWidget(self.board_widget)
        self.set_pieces(self.board.get_state())
        self.show()

    # Sets pieces in GUI according to logic board.
    # @param board_state: a representation of the current logic board state
    def set_pieces(self, board_state):
        board_coords = [(r, c) for r in range(8) for c in range(8)]
        for r, c in board_coords:
            color, kind = board_state[r][c]
            gui_r, gui_c = self.board_to_gui_coords((r, c))
            square = self.board_squares[gui_r][gui_c]
            if color and kind:
                square.place_piece(color, kind)
            elif (color, kind) == (None, None):
                square.remove_piece()

    # @param: a square that has been double clicked to lift a piece
    def lift_piece(self, square):
        self.origin_square = square
        self.piece_lifted = True

    # @param square: a square that was double clicked    
    def handleDoubleClick(self, square):
        if square.piece and not self.piece_lifted:
            self.lift_piece(square)
        elif self.piece_lifted:
            try:
                self.piece_lifted = False
                origin = self.square_to_board_coords(self.origin_square)
                target = self.square_to_board_coords(square)
                move_return = self.board.move_piece(origin, target)
            except Exception as e:
                print(e)
                self.origin_square = None
            else:
                self.set_pieces(self.board.get_state())
                if move_return.promotion:
                    self.promote_dialog()


if __name__=="__main__":
    app = QtWidgets.QApplication([])
    mw = BoardWindow()
    app.exec_()
