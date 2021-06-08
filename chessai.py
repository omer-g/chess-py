from chesslogic import *
import random


# Base class for AIs
class BaseAI:
    def __init__(self, board, is_white, name):
        # Composition
        self.board = board
        self.name = name
        self.is_white = is_white

    # Virtual function
    def get_ai_move(self):
        raise NotImplementedError("AI should implement get_ai_move function")


# Plays moves randomly
class RandomPlayer(BaseAI):
    def __init__(self, board, is_white=False):
        super().__init__(board, is_white, "random player")

    def get_ai_move(self):
        moves = self.board.generate_moves()
        return random.choice(moves)


class MinMaxPlayer(BaseAI):
    pass


class NegaMax(BaseAI):
    pass


class MonteCarlo(BaseAI):
    pass


class MinMaxMonteCarlo(BaseAI):
    pass
