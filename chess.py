from typing import Union
from definitions import *
from exceptions import *
from functools import partial
from collections import deque

# Search "API START" for interface functions
class Board:
    player_colors = { True: Colors.White, False: Colors.Black }

    # @param white_turn: Whose turn is it
    # @param state: a table of (Colors, Piece) tuples
    def __init__(self, white_turn = True, state = None):
        self.white_turn = white_turn
        self.en_passant_pawn = None
        self.promotion_coords = None
        self.moves_record = deque()

        board = [[] for i in range(DIM)]
        for r in range(len(board)):
            board[r] = tuple([Square(Coords(r, c)) for c in range(DIM)])

        self.board = tuple([tuple([sq for sq in row]) for row in board])
        # TODO set pieces according to state input
        self._place_pieces()

    def __str__(self):
        cols = "abcdefgh"
        rows = "".join([str(n) for n in range(1, DIM+1)])
        output_str = "   "
        for c in cols:
            output_str += c + "  "
        output_str += "\n"
        
        for row, row_num in zip(self.board[::-1], rows[::-1]):
            output_str += row_num + " "
            row_str = "|" + "|".join([str(square) for square in row]) + "|\n"
            output_str += row_str
        return output_str

    def _get_square(self, coords) -> Square:
        return self.board[coords[0]][coords[1]]
    
    def _get_piece(self, coords):
        return self.board[coords[0]][coords[1]].piece        

    def _clear_board(self):
        for row in self.board:
            for square in row:
                square.piece = None

    # Place pieces on board at beginning of game.
    def _place_pieces(self):
        # Clear all pieces
        self._clear_board()
        for color in [Colors.White, Colors.Black]:
            row = 1 if color == Colors.White else DIM_ZERO - 1
            for i in range(DIM):
                self.board[row][i].piece = Pawn(color)

            place = {Rook: 0, Knight: 1, Bishop: 2}
            row = 0 if color == Colors.White else DIM_ZERO
            for piece in place:
                self.board[row][0 + place[piece]].piece = piece(color)
                self.board[row][DIM_ZERO - place[piece]].piece = piece(color)
            self.board[row][4].piece = King(color)
            self.board[row][3].piece = Queen(color)
 
    # @param coords: The target coordinate where eating could occur
    # @param attacker_color: The color of the attack piece
    # @return: True if there is a piece that can be eaten on the square.
    def _eatable(self, coords, attacker_color):
        piece = self._get_piece(coords)
        if not piece or piece.color == attacker_color:
            return False
        return True

    # @param coords: coordinates of straight lines piece (Q, B, R)
    # @param color: color of piece
    # @param directions: list of direction tuples [(-1,1),...] based on piece
    # @return: set of legal moves and all squares threatened by piece
    def _linear_moves(self, directions, coords, color):
        moves = set()           # Possible moves
        threatens = set()       # Squares threatened by piece
        for direction in directions:
            for i in range(1, DIM):
                square = Coords(coords[0] + direction[0] * i,
                                    coords[1] + direction[1] * i)               
                if not on_board(square):
                    break         
                # Check if not empty
                piece = self._get_piece(square)
                if piece:
                    # Check if there's piece that can be eaten
                    if self._eatable(square, color):
                        moves.add(square)
                    threatens.add(square)
                    break
                else:
                    moves.add(square)
                    threatens.add(square)
        return moves, threatens

    def _pawn_direction(self, color):
        return 1 if color == Colors.White else -1

    # @param coords: coordinates of pawn
    # @param color: color of pawn
    # @return: set of legal moves pawn can make, and squares threatened by it
    #          does not include en passant
    def _pawn_moves(self, coords, color):
        vertical = self._pawn_direction(color)
        moves, threatens = set(), set()
        
        # Forward movement
        steps = 1
        if ((coords.r == 1 and color == Colors.White) or
            (coords.r == DIM_ZERO - 1 and color == Colors.Black)):
           steps = 2
        for i in range(1, steps + 1):
            new_square = Coords((coords.r + i * vertical), coords.c)
            if not on_board(new_square) or self._get_piece(new_square):
                break
            moves.add(new_square)

        # Pawn attack moves (except en passant)
        horizontal_directions = [-1, 1]
        for horizontal_direction in horizontal_directions:
            new_square = Coords((coords.r + 1 * vertical),
                    (coords.c + horizontal_direction))
            if on_board(new_square):
                if self._eatable(new_square, color):
                    moves.add(new_square)
                threatens.add(new_square)
        return moves, threatens

    def _king_moves(self, origin, color):
        directions = ALL_DIRECTIONS
        moves, threatens = set(), set()
        for dir in directions:
            new_coords = Coords(origin[0] + dir[0], origin[1] + dir[1])
            if not on_board(new_coords):
                continue
            threatens.add(new_coords)
            target_piece = self._get_piece(new_coords)
            if not target_piece or target_piece.color != color:
                moves.add(new_coords)
        
        # Check if castling physically could be possible.
        # Does not check if king threatened.
        # TODO refactor (separate to functions)
        if self._get_piece(origin).moves_counter == 0:
            k_dirs, r_positions = (-1, 1), (0, DIM_ZERO)
            for k_dir, r_position in zip(k_dirs, r_positions):
                castle_allowed = True
                for i in range(1,3):
                    new_coords = Coords(origin[0], origin[1] + i * k_dir)
                    target_piece = self._get_piece(new_coords)
                    if target_piece:
                        castle_allowed = False
                # Check square next to rook
                rook_coords = Coords(origin.r, r_position)
                rook = self._get_piece(rook_coords)
                if isinstance(rook, Rook) and rook.moves_counter == 0:
                    next_to_rook = Coords(origin[0], r_position + k_dir * (-1))
                    if self._get_piece(next_to_rook):
                        castle_allowed = False
                    if castle_allowed:
                        king_target = Coords(origin[0], origin[1] + 2 * k_dir)
                        moves.add(king_target)
        return moves, threatens

    # @param origin: starting coordinates of knight
    # @param color: color of knight
    # @return: moves list and squares threatened
    def _knight_moves(self, origin, color):
        moves = set()
        threatens = set()
        for dr, dc in KNIGHT:
            target = Coords(origin[0] + dr, origin[1] + dc)
            if on_board(target):
                threatens.add(target)
                if (
                    not self._get_piece(target) or
                    self._get_piece(target).color != color
                ):
                    moves.add(target)
        return moves, threatens

    # @param coords: coordinates of a square with a piece on it
    # Updates following sets in a piece:
    #   moves: set of potential moves
    #   threatens: set of squares threatened (includes same color or empty)
    def _update_moves(self, coords):
        # Dictionary of functions that return the two sets
        piece_functions = {
            Pawn: self._pawn_moves,
            Knight: self._knight_moves,
            Rook: partial(self._linear_moves, HORIZONTAL_VERTICAL),
            Bishop: partial(self._linear_moves, DIAGONAL),
            Queen: partial(self._linear_moves, ALL_DIRECTIONS),
            King: self._king_moves
        }
        piece = self._get_piece(coords)
        piece_function = piece_functions[type(piece)]
        piece.moves, piece.threatens = piece_function(coords, piece.color)

    # Update moves and threatens of all pieces of a certain color
    def _update_all_moves(self, color):
        for row in self.board:
            for square in row:
                if square.piece and square.piece.color == color:
                    self._update_moves(square.coords)

    def _coords_under_threat(self, player_color: Colors, coords: Coords):
        enemy_color = player_color.other_color()
        for row in self.board:
            for sq in row:
                enemy_piece = sq.piece
                if enemy_piece and enemy_piece.color == enemy_color:
                    self._update_moves(sq.coords)
                    if coords in enemy_piece.threatens:
                        return True
        return False
               
    def _find_king_coords(self, king_color: Colors):
        for r in range(DIM):
            for c in range(DIM):
                piece = self._get_piece(Coords(r, c))
                if isinstance(piece, King) and piece.color == king_color:
                    return Coords(r, c)
        raise NoKingError(f"No {king_color} king on board - cannot continue")

    def _check_en_passant(self, origin, target):
        origin_piece = self._get_piece(origin)
        target_piece = self._get_piece(target)
        forward = 1 if origin_piece.color == Colors.White else -1
        if self.en_passant_pawn:
            if (
                origin[0] == self.en_passant_pawn[0] and
                origin[0] + forward == target[0] and
                target[1] == self.en_passant_pawn[1] and
                abs(target[1] - origin[1]) == 1 and
                isinstance(origin_piece, Pawn) and
                not target_piece
            ):
                return True
        return False

    # @param move: List of origin and target tuples of Coords.
    #              (origin, None) for an en passant victim pawn.
    # @return: None. Performs move on board and updates the moves record
    def _move_no_checks(self, move):
        move_steps = move
        move_record = []
        for step in move_steps:
            origin, target = step
            if target:
                origin_square = self._get_square(origin)
                move_record.append(Record(origin, origin_square.piece))
                target_square = self._get_square(target)
                move_record.append(Record(target, target_square.piece))
                target_square.piece = origin_square.piece
                target_square.piece.moves_counter += 1
                origin_square.piece = None
            else:
                # This is the en passant victim pawn
                origin_square = self._get_square(origin)
                move_record.append(Record(origin, origin_square.piece))
                origin_square.piece = None
        self.moves_record.append(move_record)

    def _move_castle(self, origin, target):
        castling_options = {2: (DIM_ZERO, -2, 1), -2: (0, 3, -1)}
        column_diff = target.c - origin.c
        rook_column, rook_delta, king_dir = castling_options[column_diff]
        king = self._get_piece(origin)
        color = king.color
        rook_coords = Coords(origin.r, rook_column)
        rook = self._get_piece(rook_coords)
        if (rook.moves_counter > 0 or
            king.moves_counter > 0 or
            rook.color != color
        ):
            raise IllegalMoveException("Cannot castle")
        # Check king's path for threats
        for i in range(3):
            new_coords = Coords(origin.r, origin.c + i * king_dir)
            if self._coords_under_threat(color, new_coords):
                raise KingThreatenedException("Cannot castle under threat")

        # Perform castling
        rook_target = Coords(rook_coords.r, rook_coords.c + rook_delta)
        self._move_no_checks([(origin, target), (rook_coords, rook_target)])

    def _revert(self):
        if len(self.moves_record) == 0:
            raise RevertException("Cannot revert start position")
        prev_move = self.moves_record.pop()
        for record in prev_move:
            square = self._get_square(record.coords)
            if record.piece_type:
                square.piece = record.piece_type(record.color,
                                                 record.moves_counter)
            else:
                square.piece = None

    # @param origin, target: coordinates of a quasi-legal move
    # @param passant_victim: coordinates of en passant victim
    def _perform_move(self, origin, target, passant_coords = None):

        origin_piece = self._get_piece(origin)
        move = [(origin, target)]

        # Castle
        if isinstance(origin_piece, King) and abs(target[1] - origin[1]) == 2:
            # King safety checked inside
            self._move_castle(origin, target)
        else:
            # En passant
            if passant_coords:
                move.append((passant_coords, None))
            self._move_no_checks(move)
            # Check king safety and revert if needed
            king_coords = self._find_king_coords(origin_piece.color)
            if self._coords_under_threat(origin_piece.color, king_coords):
                self._revert()
                raise KingThreatenedException("King under threat")

    def _pawn_two_squares(self, origin, target):
        if isinstance(self._get_piece(target), Pawn):
            if abs(origin[0] - target[0]) == 2:
                return target
        return None

    def _check_promotion(self, target: Coords) -> Union[Coords, None]:
        piece = self._get_piece(target)
        if isinstance(piece, Pawn):
            if (
                piece.color == Colors.White and target.r == DIM_ZERO or
                piece.color == Colors.Black and target.r == 0
            ):
                return target
        return None

    def _legal_move_exists(self, color):
        self._update_all_moves(color)
        for row in self.board:
            for square in row:
                piece = square.piece
                if piece and piece.color == color:
                    for move in piece.moves:
                        try:
                            self._perform_move(square.coords, move)
                        except ValueError as e:
                            continue
                        else:
                            # Legal move found, revert.
                            self._revert()
                            return True
        return False        

    def _check_mate(self, king_color):
        # TODO write more efficient version:
            # Check if double threat
            # Check pinned pieces
            # Check if any piece can block or eat
            # Check if king can move
        return not self._legal_move_exists(king_color)


########################### API START ###########################

    # @param color: current player
    # @return: status of game (check, checkmate, stalemate)
    def get_status(self, color):
        opponent_color = color.other_color()
        opponent_king = self._find_king_coords(opponent_color)

        game_status = BoardStatus.Normal
        if self._coords_under_threat(opponent_color, opponent_king):
            game_status = BoardStatus.Check
            if self._check_mate(opponent_color):
                print("Checkmate")
                game_status = BoardStatus.Checkmate
            else:
                print("Check")
        # TODO stalemate
        elif not self._legal_move_exists(opponent_color):
            game_status = BoardStatus.Stalemate
            print("Stalemate")
        return game_status

    # @return: Board with (color, piece-type) tuples or (None, None)
    def get_state(self):
        board_state = [[] for _ in range(DIM)]
        for i, row in enumerate(self.board):
            for square in row:
                color = square.piece.color if square.piece else None
                piece_type = type(square.piece) if square.piece else None
                board_state[i].append(((color, piece_type)))
        return board_state

    def revert_last_move(self):
        try:
            self._revert()
            self.white_turn = not self.white_turn
        except Exception as e:
            print(e)

    # @param piece_type: The piece type the user chooses
    # @return: A MoveReturn with the current board status.
    def promote_pawn(self, piece_type):
        if not self.promotion_coords:
            raise RuntimeError("Error - no pawn to promote")
        coords = self.promotion_coords
        self.promotion_coords = None
        piece = self._get_piece(coords)
        square = self._get_square(coords)
        color = piece.color
        square.piece = piece_type(color)
        game_status = self.get_status(color)
        return MoveReturn(game_status, None)

    # @param origin: start coordinate of move
    # @param target: end coordinate
    def move_piece(self, origin: Coords, target: Coords) -> MoveReturn:
        if self.promotion_coords:
            raise PromotionWaitException("Choose pawn promotion")
        if not on_board(origin) or not on_board(target):
            raise NotOnBoardException("Coordinates not on board")
        if origin == target:
            raise SameSquareException("Same square")
        origin_piece = self._get_piece(origin)
        if not origin_piece:
            raise NoPieceException(f"No piece in {origin}")
        if origin_piece.color != Board.player_colors[self.white_turn]:
            raise WrongTurnException("Not your turn")

        target_piece = self._get_piece(target)
        if target_piece and target_piece.color == origin_piece.color:
            raise SameColorException("Same color")
        self._update_moves(origin)

        do_en_passant = self._check_en_passant(origin, target)
        if target in origin_piece.moves or do_en_passant:
            if do_en_passant:
                self._perform_move(origin, target, self.en_passant_pawn)
            else:
                self._perform_move(origin, target)
            # If pawn double-traveled en passant may be possible next move
            self.en_passant_pawn = self._pawn_two_squares(origin, target)
            self.white_turn = not self.white_turn
            self.promotion_coords = self._check_promotion(target)
            game_status = self.get_status(origin_piece.color)
            return MoveReturn(status=game_status,
                              promotion=self.promotion_coords)
        else:
            raise IllegalMoveException(f"Illegal move: {origin, target}")

############################ API END ############################


# Console interface

def text_to_coords(coords_str):
    if len(coords_str) != 2:
        raise ValueError(f"Invalid coordinates: {coords_str}")

    letter_num = {}
    for i, c in enumerate("abcdefgh"):
        letter_num[c] = i
    nums = "12345678"

    letter, num = coords_str
    if not letter in letter_num or not num in nums:
        raise ValueError(f"Invalid coordinates: {coords_str}")

    r, c = int(num) - 1, letter_num[letter]
    return Coords(r, c)


def console_promote(board):
    char_to_piece = {"Q": Queen, "R": Rook, "B": Bishop, "N": Knight}
    print(board)
    print("Choose promotion (Q, R, B, N):")
    while True:
        try: 
            choice = input()
            if choice not in list("QRBN"):
                raise ValueError("Invalid promotion choice, try again:")
            board.promote_pawn(char_to_piece[choice])
        except ValueError as e:
            print(e)
        else:
            break


if __name__=="__main__":
    board = Board()
    print("chess-py console\n")
    print("Move: 'e2 e4'\nRevert last move: 'r'\nExit: '0'\n")
    print(board)
    while True:
        print("Enter move:")
        move_input = input()
        if move_input == 'r':
            try:
                board.revert_last_move()
            except Exception as e:
                print(e)
            finally:
                print(board)
                continue
        if move_input == '0':
            break
        try:
            start, end = move_input.split(" ")
            move = board.move_piece(text_to_coords(start), text_to_coords(end))
            if move.promotion:
                console_promote(board)
            if move.status == BoardStatus.Checkmate:
                break
        except ValueError as e:
            print(e)
        finally:
            print(board)
