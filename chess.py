from typing import Union
from definitions import *
from exceptions import *
from functools import partial
from collections import deque
import sys

# Search "API START" for interface functions

class Board:
    piece_types = [Pawn, Rook, Knight, Bishop, Queen, King]
    player_colors = { True: Colors.White, False: Colors.Black }

    # @param white_turn: Whose turn is it
    # @param fen_position: a board position in FEN format
    def __init__(self, white_turn = True, position = None):
        self.white_turn = white_turn
        self.passant_pawn = None
        self.promotion_coords = None
        self.moves_record = deque()
        self.game_status = BoardStatus.Normal

        # Store coordinates for each piece type 
        self.white_pieces = dict((piece, set()) for piece in self.piece_types)
        self.black_pieces = dict((piece, set()) for piece in self.piece_types)
        self.pieces = {Colors.White: self.white_pieces,
                       Colors.Black: self.black_pieces
        }

        # Set board
        self.board = tuple([tuple([Square(Coords(r, c))
                            for c in range(DIM)]) for r in range(DIM)]
        )
        self.start_position = position if position else START_POSITION
        self._set_pieces(self.start_position)

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

    def _clear_board(self):
        for row in self.board:
            for square in row:
                piece = square.piece
                coords = square.coords
                if piece:
                    self.pieces[piece.color][type(piece)].remove(coords)
                    square.piece = None

    def _set_piece(self, coords, piece):
        self.board[coords[0]][coords[1]].piece = piece
        self.pieces[piece.color][type(piece)].add(coords)

    # TODO process a complete FEN record
    # @param board_str: A FEN-format piece placement string (first field only)
    def _set_pieces(self, board_str):
        self._clear_board()
        # Black ranks first
        position = [DIM_ZERO, 0]
        char_to_piece = {
            "P": Pawn,
            "R": Rook,
            "N": Knight,
            "B": Bishop,
            "Q": Queen,
            "K": King
        }
        for c in board_str:
            # Create piece and place on board
            if c.upper() in char_to_piece:
                color = Colors.White if c.isupper() else Colors.Black
                piece = char_to_piece[c.upper()](color)
                coords = Coords(position[0], position[1])

                self._set_piece(coords, piece)
                position[1] = (position[1] + 1) % DIM
            # Skip empty squares in rank
            if c in "12345678":
                empty_squares = int(c)
                position[1] = (position[1] + empty_squares) % DIM
            # Next rank
            if c == "/":
                position[0] -= 1
            # In order to be able to read a full FEN record - change later
            if c ==" ":
                break

    def _get_square(self, coords) -> Square:
        return self.board[coords[0]][coords[1]]
    
    def _get_piece(self, coords):
        return self.board[coords[0]][coords[1]].piece        

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
                new_coords = Coords(coords[0] + direction[0] * i,
                                    coords[1] + direction[1] * i)               
                if not on_board(new_coords):
                    break         
                # Check if not empty
                piece = self._get_piece(new_coords)
                if piece:
                    # Check if there's piece that can be eaten
                    if self._eatable(new_coords, color):
                        moves.add((new_coords, None))
                    threatens.add(new_coords)
                    break
                else:
                    moves.add((new_coords, None))
                    threatens.add(new_coords)
        return moves, threatens

    def final_row(self, row, color: Colors):
        return ((color == Colors.White and row == DIM_ZERO) or
                (color == Colors.Black and row == 0)
        )

    def _pawn_direction(self, color):
        return 1 if color == Colors.White else -1

    # @param coords: coordinates of pawn
    # @param color: color of pawn
    # @return: set of legal moves pawn can make, and squares threatened by it
    #          does not include en passant
    def _pawn_moves(self, coords, color):
        vertical = self._pawn_direction(color)
        moves, threatens = set(), set()
        
        promote = self.final_row(coords.r + 1 * vertical, color)
        # Forward movement
        steps = 1
        if ((coords.r == 1 and color == Colors.White) or
            (coords.r == DIM_ZERO - 1 and color == Colors.Black)):
           steps = 2
        for i in range(1, steps + 1):
            new_coords = Coords((coords.r + i * vertical), coords.c)
            if not on_board(new_coords) or self._get_piece(new_coords):
                break
            if promote:
                for promote_type in PROMOTE:
                    moves.add((new_coords, promote_type))
            else:
                moves.add((new_coords, None))

        # Pawn attack moves (except en passant)
        horizontal_directions = [-1, 1]
        for horizontal_direction in horizontal_directions:
            new_coords = Coords((coords.r + 1 * vertical),
                    (coords.c + horizontal_direction))
            if on_board(new_coords):
                if self._eatable(new_coords, color):
                    if promote:
                        for promote_type in PROMOTE:
                            moves.add((new_coords, promote_type))
                    else:
                        moves.add((new_coords, None))
                threatens.add(new_coords)
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
                moves.add((new_coords, None))
        
        # Check if castling physically could be possible.
        # Does not check if king threatened.
        # TODO refactor (separate to functions)
        piece = self._get_piece(origin)
        if piece.moves_counter == 0:
            king_dirs, r_positions = (-1, 1), (0, DIM_ZERO)
            for king_dir, rook_pos in zip(king_dirs, r_positions):
                castle_allowed = True
                for i in range(1,3):
                    new_coords = Coords(origin[0], origin[1] + i * king_dir)
                    target_piece = self._get_piece(new_coords)
                    if target_piece:
                        castle_allowed = False
                # Check square next to rook
                rook_coords = Coords(origin.r, rook_pos)
                rook = self._get_piece(rook_coords)
                if isinstance(rook, Rook) and rook.moves_counter == 0:
                    next_to_rook = Coords(origin[0], rook_pos + king_dir * (-1))
                    if self._get_piece(next_to_rook):
                        castle_allowed = False
                    if castle_allowed:
                        # Calculate target square of king
                        target = Coords(origin[0], origin[1] + 2 * king_dir)
                        moves.add((target, None))
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
                    moves.add((target, None))
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
        if self.passant_pawn:
            if (
                origin[0] == self.passant_pawn[0] and
                origin[0] + forward == target[0] and
                target[1] == self.passant_pawn[1] and
                abs(target[1] - origin[1]) == 1 and
                isinstance(origin_piece, Pawn) and
                not target_piece
            ):
                return True
        return False

    def _save_coords(self, coords, piece):
        if piece:
            coords_list = self.pieces[piece.color][type(piece)]
            coords_list.add(coords)

    def _remove_coords(self, coords, piece):
        if piece:
            try:
                coords_list = self.pieces[piece.color][type(piece)]
                coords_list.remove(coords)
            # TODO change back to ValueError?
            except Exception as e:
                print("attempt to remove coords not in pieces", coords, piece)
                print(type(e).__name__, e)


    # @param move: List of origin, target tuples of Coords.
    #              (origin, None) for an en passant victim pawn.
    # @return: None. Performs move on board and updates the moves record
    def _move_no_checks(self, move, promote_type = None):
        move_steps = move
        move_record = (self.passant_pawn, self.promotion_coords, [])
        for step in move_steps:
            origin, target = step
            if target:
                origin_square = self._get_square(origin)
                move_record[2].append(Record(origin, origin_square.piece))
                self._remove_coords(origin, origin_square.piece)
                
                target_square = self._get_square(target)
                move_record[2].append(Record(target, target_square.piece))
                self._remove_coords(target, target_square.piece)

                if promote_type == None:
                    target_square.piece = origin_square.piece
                    target_square.piece.moves_counter += 1
                else:
                    target_square.piece = promote_type(origin_square.piece.color)
                self._save_coords(target, target_square.piece)
                origin_square.piece = None
            else:
                # This is the en passant victim pawn
                origin_square = self._get_square(origin)
                move_record[2].append(Record(origin, origin_square.piece))
                self._remove_coords(origin, origin_square.piece)
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
            raise IllegalMoveException("cannot castle")
        # Check king's path for threats
        for i in range(3):
            new_coords = Coords(origin.r, origin.c + i * king_dir)
            if self._coords_under_threat(color, new_coords):
                raise KingThreatenedException("cannot castle under threat")

        # Perform castling
        rook_target = Coords(rook_coords.r, rook_coords.c + rook_delta)
        self._move_no_checks([(origin, target), (rook_coords, rook_target)])

    def _revert(self):
        # TODO store all state inforation in Record (en passant status etc)
        if len(self.moves_record) == 0:
            raise RevertException("cannot revert start position")
        passant_pawn, promotion_coords, prev_move = self.moves_record.pop()
        self.passant_pawn = passant_pawn
        self.promotion_coords = promotion_coords
        for record in prev_move:
            square = self._get_square(record.coords)
            self._remove_coords(record.coords, square.piece)
            if record.piece_type:
                square.piece = record.piece_type(record.color,
                                                 record.moves_counter)
                self._save_coords(record.coords, square.piece)
            else:
                square.piece = None

    # @param origin, target: coordinates of a quasi-legal move
    # @param passant_victim: coordinates of en passant victim
    def _perform_move(self, origin, target_tuple, passant_coords = None):
        target, promote_type = target_tuple
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
            self._move_no_checks(move, promote_type)
            # Check king safety and revert if needed
            king_coords = self._find_king_coords(origin_piece.color)
            if self._coords_under_threat(origin_piece.color, king_coords):
                self._revert()
                raise KingThreatenedException("king under threat")

    def _pawn_two_squares(self, origin, target):
        if isinstance(self._get_piece(target), Pawn):
            if abs(origin[0] - target[0]) == 2:
                return target
        return None

    def _check_promotion(self, target: Coords, piece) -> Union[Coords, None]:
        # TODO add origin too
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
                            # Legal move found - revert it.
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

    # TODO this might be redundant if threats are checked anyway
    # @param coords: Coordinates of king
    # @param king_color: Color of king
    # @return: lists of pieces that threaten king
    #          and pinned pieces with (Coords, Piece) tuples
    def _check_king_threats(self, coords: Coords, king_color: Colors):
        piece_dir = {
            Rook: HORIZONTAL_VERTICAL,
            Bishop: DIAGONAL,
            Queen: ALL_DIRECTIONS                    
        }
        # Tuples of (coords, piece)
        pinned_pieces = []
        threats = []

        # Check long distance threats and pins
        for dir in ALL_DIRECTIONS:
            potential_pin = None
            for i in range(1, DIM):
                new_coords = Coords(coords.r + dir[0] * i, coords.c + dir[1])
                if not on_board(new_coords):
                    break
                piece = self._get_piece(new_coords)
                if piece:
                    if piece.color == king_color:
                        potential_pin = (new_coords, piece)
                    if (piece.color == king_color.other_color() and
                        type(piece) in piece_dir and
                        dir in piece_dir[type(piece)]  
                    ):
                        if potential_pin:
                            pinned_pieces.append(potential_pin)
                        else:
                            threats.append((new_coords, piece))
                        break
        # Check knight threats
        for delta in KNIGHT:
            new_coords = Coords(coords.r + delta[0], coords.c + delta[1])
            if on_board(new_coords):
                piece = self._get_piece(new_coords)
                if type(piece) is Knight:
                    threats.append((new_coords, piece))
        # Check pawn threat
        direction = 1 if king_color == Colors.White else -1
        left_right = [-1, 1]
        for horizontal_dir in left_right:
            new_coords = (coords.r + direction, coords.c + horizontal_dir)
            if on_board(new_coords):
                piece = self._get_piece(new_coords)
                if (type(piece) is Pawn and
                    piece.color == king_color.other_color()
                ):
                    threats.append((new_coords, piece))
        
        return threats, pinned_pieces


    def _calc_threats(self, color: Colors):
        pieces = self.pieces[color]
        for piece_type in pieces:
            coords_list = pieces[piece_type]
            for coords in coords_list:
                piece = self._get_piece(coords)
                

########################### API START ###########################

    # @param color: current player
    # @return: status of game (check, checkmate, stalemate)
    def update_status(self, color):
        opponent_color = color.other_color()
        opponent_king = self._find_king_coords(opponent_color)

        self.game_status = BoardStatus.Normal
        if self._coords_under_threat(opponent_color, opponent_king):
            self.game_status = BoardStatus.Check
            if self._check_mate(opponent_color):
                print("checkmate")
                self.game_status = BoardStatus.Checkmate
            else:
                print("check")
        elif not self._legal_move_exists(opponent_color):
            self.game_status = BoardStatus.Stalemate
            print("stalemate")
        return self.game_status

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

    # TODO remove this
    # @param piece_type: The piece type the user chooses
    # @return: A MoveReturn with the current board status.
    def promote_pawn(self, piece_type):
        if not self.promotion_coords:
            raise RuntimeError("error - no pawn to promote")
        # TODO Record missing
        coords = self.promotion_coords
        self.promotion_coords = None
        piece = self._get_piece(coords)
        square = self._get_square(coords)
        color = piece.color
        # TODO remove pawn from coords dict and then place piece
        self._remove_coords(coords, piece)
        square.piece = piece_type(color)
        self._save_coords(coords, square.piece)
        game_status = self.update_status(color)
        return MoveReturn(game_status, None)

    # @param origin: start coordinate of move
    # @param target: end coordinate
    # @param promotion: type of promotion piece or None
    def move_piece(self, origin, target, promotion) -> MoveReturn:
        if not on_board(origin) or not on_board(target):
            raise NotOnBoardException("coordinates not on board")
        if origin == target:
            raise SameSquareException("same square")
        origin_piece = self._get_piece(origin)
        if not origin_piece:
            raise NoPieceException(f"no piece in {origin}")
        if origin_piece.color != Board.player_colors[self.white_turn]:
            raise WrongTurnException("not your piece")

        target_piece = self._get_piece(target)
        if target_piece and target_piece.color == origin_piece.color:
            raise SameColorException("same color")
        
        if self._check_promotion(target, origin_piece):
            if promotion not in PROMOTE:
                raise MissingPromotionChoice("retry move with promotion choice")

        self._update_moves(origin)
        do_en_passant = self._check_en_passant(origin, target)
        if (any(target in move for move in origin_piece.moves)) or do_en_passant:
            if do_en_passant:
                self._perform_move(origin, (target, promotion), passant_coords=self.passant_pawn)
            else:
                self._perform_move(origin, (target, promotion))
            # If pawn double-traveled en passant may be possible next move
            self.passant_pawn = self._pawn_two_squares(origin, target)
            self.white_turn = not self.white_turn
            target_piece = self._get_piece(target)
            self.promotion_coords = self._check_promotion(target, target_piece)
            game_status = self.update_status(origin_piece.color)
            return game_status
        else:
            raise IllegalMoveException(f"illegal move {origin, target}")

############################ API END ############################


# Console interface

def text_to_coords(coords_str):
    if len(coords_str) != 2:
        raise ValueError(f"invalid coordinates {coords_str}")

    letter_num = {}
    for i, c in enumerate("abcdefgh"):
        letter_num[c] = i
    nums = "12345678"

    letter, num = coords_str
    if not letter in letter_num or not num in nums:
        raise ValueError(f"invalid coordinates {coords_str}")

    r, c = int(num) - 1, letter_num[letter]
    return Coords(r, c)


def console_promote(board, file_moves, origin, target):
    print(board)
    print("choose promotion piece (Q, R, B, N)")
    while True:
        try: 
            choice = file_moves.pop(0) if len(file_moves) > 0 else input()
            if choice == "0":
                return None
            if choice not in list("QRBN"):
                raise ValueError("invalid choice try again")
        except ValueError as e:
            print(e)
        else:
            return CHAR_PROMOTE[choice]

def text_to_promotion(s):
    return None if s is None else CHAR_PROMOTE[s]

if __name__=="__main__":
    board = Board()
    print(INTRO)    
    print("move: 'e2 e4' or 'a7 a8 Q' revert: 'r' exit: '0'\n")
    print(board)

    file_moves = []
    if len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            for line in f:
                file_moves.append(line.strip())
    while True:
        print("enter move")
        move_input = file_moves.pop(0) if len(file_moves) > 0 else input()
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
            start, end, promote_choice = None, None, None
            move_split = move_input.split(" ")
            if len(move_split) == 2:
                start, end = move_split
            elif len(move_split) == 3:
                start, end, promote_choice = move_split

            origin = text_to_coords(start)
            target = text_to_coords(end)
            promotion = text_to_promotion(promote_choice)
            move_return = board.move_piece(origin, target, promotion)
            print(board)
        except MissingPromotionChoice as e:
            promotion = console_promote(board, file_moves, origin, target)
            if promotion == None:
                break
            move_return = board.move_piece(origin, target, promotion)            
            print(board)
        except ValueError as e:
            print(e)
        finally:
            if (move_return == BoardStatus.Checkmate or
                move_return == BoardStatus.Stalemate
            ):
                break            
