from chesslogic import *
import random
import math

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
        print("initialize random player")

    def get_ai_move(self):
        moves = self.board.generate_moves()
        return random.choice(moves)


class MinMaxPlayer(BaseAI):
    def __init__(self, board, is_white, heuristic, depth = 1):
        super().__init__(board, is_white, "minmax player")
        self.heuristic = heuristic
        print("initialize minmax player\ndepth:", depth)
    
    def _min_max_rec(self, maximize, depth, root_white):
        if depth == 0:
            h = self.heuristic(self.board)
            return h if root_white else -h
        else:
            moves = self.board.generate_moves()
            best_score = -math.inf if maximize else math.inf
            # TODO refactor this
            for move in moves:
                origin, target, promotion = move
                try:
                    self.board.move_piece(origin, target, promotion)
                except:
                    # TODO could pop illegal moves
                    # TODO handle case where no moves
                    continue
                score = self._min_max_rec(not maximize, depth - 1, root_white)
                if ((maximize and score > best_score) or
                    (not maximize and score < best_score)
                ):
                    best_score = score
                self.board.revert_last_move()
        return best_score

    # @param maximize: maximize on AI turn, minimize opponent turn
    # @param depth: depth of recursion. at least 1.
    def _min_max(self, depth):
        maximize = True
        moves = self.board.generate_moves()
        best_move = None
        best_score = -math.inf if maximize else math.inf
        # TODO refactor this?
        root_is_white = self.board.white_turn
        for move in moves:
            origin, target, promotion = move
            try:
                self.board.move_piece(origin, target, promotion)
            except ValueError as e:
                print(e)
                # TODO could pop illegal moves
                continue
            score = self._min_max_rec(not maximize, depth - 1, root_is_white)
            if ((maximize and score > best_score) or
                (not maximize and score < best_score)
            ):
                best_score = score
                best_move = move
            self.board.revert_last_move()
        return best_move

    def get_ai_move(self):
        return self._min_max(1)


class NegaMax(BaseAI):
    pass


class MonteCarlo(BaseAI):
    pass


class MinMaxMonteCarlo(BaseAI):
    pass

material_value = {Pawn: 1, Knight: 3, Bishop: 3, Rook: 5, Queen: 9, King: 0}

def material_heuristic(board: Board):
    score = 0
    for piece_type in board.white_pieces:
        score += len(board.white_pieces[piece_type]) * material_value[piece_type]
    for piece_type in board.black_pieces:
            score -= len(board.black_pieces[piece_type]) * material_value[piece_type]
    return score

