from collections import namedtuple
from chessenums import Pieces, Colors


# Board dimensions
DIM = 8
DIM_ZERO = 7

# Directions for straight movement
DIAGONAL = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
HORIZONTAL_VERTICAL = [(1, 0), (-1, 0), (0, 1), (0, -1)]

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
    """A piece"""

    def __init__(self, color, text):
        self.color = color
        self.text = text
    
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
    """A square on the board"""

    def __init__(self, color):
        self.color = color
        self.piece = None

    def __str__(self):
        return self.piece.__str__() if self.piece else "  "
    
    __repr__ = __str__


class Board:
    """A simple board"""
    player_color = { True: Colors.White, False: Colors.Black }


    def __init__(self, white_turn = True):
        self.white_turn = white_turn

        board = [[] for i in range(DIM)]
        for i, _ in enumerate(board):
            board[i] = tuple([Square((j + i) % 2  == 0) for j in range(DIM)])

        # Create empty board
        self.board = tuple([tuple([square for square in row]) for row in board])
        self.place_pieces()

    # Place pieces on the board at the beginning of the game.
    def place_pieces(self):
        for color in [Colors.White, Colors.Black]:
            row = 1 if color == Colors.White else DIM_ZERO - 1
            for i in range(DIM):
                self.board[row][i].piece = Pawn(color)

            relative_place = {Rook: 0, Knight: 1, Bishop: 2}
            row = 0 if color == Colors.White else DIM_ZERO
            for key_piece in relative_place:
                self.board[row][0 + relative_place[key_piece]].piece = key_piece(color)
                self.board[row][DIM_ZERO - relative_place[key_piece]].piece = key_piece(color)
            self.board[row][4].piece = King(color)
            self.board[row][3].piece = Queen(color)
 
    def get_square(self, coords):
        return self.board[coords.r][coords.c]
    
    def get_piece(self, coords):
        return self.board[coords.r][coords.c].piece        

    # @param coords: The target coordinate where eating could occur
    # @param attacker_color: The color of the attack piece
    # @return: True if there is a piece that can be eaten on the square.
    def eatable(self, coords, attacker_color):
        piece = self.get_piece(coords)
        if not piece or piece.color == attacker_color:
            return False
        return True
    
    def in_range(self, num):
        return num >= 0 and num < DIM

    # @param coords: coordinates of a piece that moves in straight lines (Q, B, R)
    # @param color: color of piece
    # @param directions_list: a list of direction tuples [(-1,1),...] based on piece.
    # @return: set of legal moves the piece can make
    def get_moves_in_straight_lines(self, coords, color, directions_list):
        moves = set()
        for direction in directions_list:
            for i in range(1, DIM):
                new_square = Coords(coords[0] + direction[0] * i, coords[1] + direction[1] * i)               
                # Check out of range
                if not on_board(new_square):
                    break         
                # Check if not empty
                piece_in_new_square = self.get_piece(new_square)
                if piece_in_new_square:
                    # If there is a piece that can be eaten add square to legal squares
                    if self.eatable(new_square, color):
                        moves.add(new_square)
                    break
                else:
                    # Add empty square to legal squares
                    moves.add(new_square)
        return moves

    # @param coords: coordinates of pawn
    # @param color: color of pawn
    # @return: set of legal moves the pawn can make
    def get_moves_of_pawn(self, coords, color):
        vertical_direction = 1 if color == Colors.White else -1
        moves = set()
        
        # Forward movement
        steps = 1
        if (coords.r == 1 and color == Colors.White) or (coords.r == DIM_ZERO - 1 and color == Colors.Black):
           steps = 2
        for i in range(1, steps + 1):
            new_square = Coords((coords.r + i * vertical_direction), coords.c)
            if not on_board(new_square) or self.get_piece(new_square):
                break
            moves.add(new_square)

        # Check eating
        right_left = [-1, 1]
        for horizontal_direction in right_left:
            new_square = Coords((coords.r + 1), (coords.c + 1 * horizontal_direction))
            if on_board(new_square) and self.eatable(new_square, color):
                moves.add(new_square)

        # TODO add en passant later
        return moves

    def get_moves_of_king(self, origin, color):
        directions = HORIZONTAL_VERTICAL + DIAGONAL
        moves = set()
        for direction in directions:
            new_square = Coords(origin[0] + direction[0], origin[1] + direction[1])
            if not on_board(new_square):
                continue
            target_piece = self.get_piece(new_square)
            if not target_piece or target_piece.color != color:
                # TODO here add a check if target square is threatened by other color
                moves.add(new_square)

        # Check castling
        # TODO rewrite reduce numbers etc.
        if self.get_piece(origin).can_castle == True:
            k_dirs, r_positions, r_deltas = (-1, 1), (0, DIM_ZERO), (3, -2)
            for k_dir, r_position, r_delta in zip(k_dirs, r_positions, r_deltas):
                castle_allowed = True
                for i in range(1,3):
                    new_square = Coords(origin[0], origin[1] + i * k_dir)
                    target_piece = self.get_piece(new_square)
                    if target_piece:
                        castle_allowed = False
                # Check square next to rook
                next_to_rook = Coords(origin[0], r_position + k_dir * (-1))
                if self.get_piece(next_to_rook):
                    castle_allowed = False
                if castle_allowed:
                    king_castle_target = Coords(origin[0], origin[1] + 2 * k_dir)
                    moves.add(king_castle_target)
        return moves

    # @param a, b: coordinates (can be regular tuples as well)
    # @return: tuple of difference
    @staticmethod
    def sub_coords(a, b):
        return (a[0] - b[0], a[1] - b[1])

    # @param delta: the difference between origin and target
    # @return: True if the delta between squares fits the movement of a knight.
    def knight_movement(self, origin, target):
        # Get the difference between the target and the origin squares.
        delta =  self.sub_coords(target, origin)
        return set(map(abs, delta)) == {1, 2}

    # @param origin, target: coordinates of a legal move
    def __perform_move(self, origin, target):
        """Move any piece anywhere."""

        # TODO here check if King of current player would be threatened.
        #   Raise exception if he is threatened.

        piece = self.get_piece(origin)
        origin_square = self.get_square(origin)
        target_square = self.get_square(target)

        target_square.piece = piece
        origin_square.piece = None

        if type(piece) == King:
            if self.sub_coords(target, origin)[1] == 2:
                rook_coords = Coords(origin[0], DIM_ZERO)
                rook_target = Coords(origin[0], DIM_ZERO - 2)
                self.__perform_move(rook_coords, rook_target)
            if self.sub_coords(target, origin)[1] == -2:
                rook_coords = Coords(origin[0], 0)
                rook_target = Coords(origin[0], 3)
                self.__perform_move(rook_coords, rook_target)
            print(rook_coords, rook_target)


    def move_piece(self, origin, target):
        if not on_board(origin) or not on_board(target):
            raise ValueError("Not on board")        
        if origin == target:
            raise ValueError("Same square")

        origin_piece = self.get_piece(origin)
        if not origin_piece:
            raise ValueError("No piece in ", origin)
        
        if origin_piece.color != Board.player_color[self.white_turn]:
            raise ValueError("This is not your piece")

        # Check target doesn't have a piece with same color as origin.
        target_piece = self.get_piece(target)
        if target_piece and target_piece.color == origin_piece.color:
            raise ValueError("Same color")

        move_flag = False
        # Pawn
        if isinstance(origin_piece, Pawn):    
            if target in self.get_moves_of_pawn(origin, origin_piece.color):
                self.__perform_move(origin, target)
                move_flag = True
        # Knight
        if isinstance(origin_piece, Knight) and self.knight_movement(origin, target):
                self.__perform_move(origin, target)
                move_flag = True
        # Bishop
        if isinstance(origin_piece, Bishop):
            if target in self.get_moves_in_straight_lines(origin, origin_piece.color, DIAGONAL):
                self.__perform_move(origin, target)
                move_flag = True
        # Rook
        if isinstance(origin_piece, Rook):
            if target in self.get_moves_in_straight_lines(origin, origin_piece.color, HORIZONTAL_VERTICAL):
                self.__perform_move(origin, target)
                origin_piece.can_castle == False                
                move_flag = True
        # Queen
        if isinstance(origin_piece, Queen):
            if target in self.get_moves_in_straight_lines(origin, origin_piece.color, DIAGONAL + HORIZONTAL_VERTICAL):
                self.__perform_move(origin, target)
                move_flag = True
        # King
        if isinstance(origin_piece, King):
            if target in self.get_moves_of_king(origin, origin_piece.color):
                self.__perform_move(origin, target)
                origin_piece.can_castle = False
                move_flag = True

        if move_flag:
            self.white_turn = not self.white_turn
            return True
        else:
            raise ValueError("Illegal move: ", origin, target)


    # @return: Board with color and piece-type tuples or (None, None)
    def get_state(self):
        # No NoneType reference in types module
        NoneType = type(None)
        pieces_dict = {
            Pawn: Pieces.Pawn,
            Rook: Pieces.Rook,
            Knight: Pieces.Knight,
            Bishop: Pieces.Bishop,
            Queen: Pieces.Queen,
            King: Pieces.King,
            NoneType: None
            }
        board_state = [[] for _ in range(DIM)]
        for i, row in enumerate(self.board):
            for j, square in enumerate(row):
                color = square.piece.color if square.piece else None
                piece_type = pieces_dict[type(square.piece)]
                board_state[i].append(((color, piece_type)))
        return board_state

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


if __name__=="__main__":
    board = Board()
    print(board)
    
    p = Pawn(Colors.White)
    board.move_piece(Coords(1,4), Coords(3,4))
    # board.move_piece(Coords(3,1), Coords(2,1))
    print(board)
    print(board.knight_movement((0, 1), (2,2)))
    print(sorted(board.get_moves_in_straight_lines(Coords(3,3), Colors.White, DIAGONAL + HORIZONTAL_VERTICAL)))
    # Board.on_board(Coords(2, -1))
    print(board.get_moves_of_pawn(Coords(5,3), Colors.White))
