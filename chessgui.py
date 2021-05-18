from PyQt5 import QtWidgets
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

DIM = 1024
SQUARE = 70
PIECE = 60


# class GuiSquare():
#     def __init__(self, x, y, square_color):
#         _square = QFrame(self)

class MainWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(qtw.QGridLayout())
        self.resize(DIM,DIM)        
        
        board = [[] for _ in range(0, 8)]
        for r, row in enumerate(board):
            for c in range(0, 8):
                square = QFrame(self)
                square.setObjectName(u"frame" + f"{r}-{c}")
                square.setGeometry(QRect(DIM // 2 - SQUARE * 4 + SQUARE * c,
                                        DIM - 300 - SQUARE*(r+1), SQUARE, SQUARE))
                if (r + c) % 2 == 0:
                    square.setStyleSheet(u"background-color: grey;")
                else:
                    square.setStyleSheet(u"background-color: white;")
                row.append(square)
        self.setStyleSheet("MainWindow {background-color: rgb(0,139,139);}") 
        
        self.setWindowFlag(Qt.FramelessWindowHint)


        pawn = QtWidgets.QLabel(self)
        pawn.setPixmap(qtg.QPixmap("pieces/b_pawn.png"))
        print(board[0][0].pos())
        pawn.setGeometry(board[3][0].pos().x() + 5 , board[3][0].pos().y() + 5, PIECE, PIECE)
        self.show()

app = qtw.QApplication([])
mw = MainWindow()
app.exec_()
