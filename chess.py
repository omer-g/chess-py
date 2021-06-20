from chessai import MinMaxPlayer, RandomPlayer, material_heuristic
from chesslogic import *
import random
import argparse

# Terminal interface

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


def text_to_promotion(s):
    return None if s is None else CHAR_PROMOTE[s]


# @return: Type of promotion piece chosen
#          None to quit game
def ask_promote(board, file_moves):
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


def end_game(game_status):
    return (game_status == BoardStatus.Checkmate or
        game_status == BoardStatus.Stalemate
    )


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="path to test file")
    parser.add_argument("-ai", "--ai", help="play against AI: r - random"
                        "m - minmax"                    
    )
    parser.add_argument("-d", "--depth", default=1, help="depth for recursive"
                        "algorithms should be 1 or more (default 1)"
    )
    parser.add_argument("-c", "--color",
                        help="color of human player: b - black, w - white"
    )

    print(INTRO)
    print("move: 'e2 e4' or 'a7 a8 Q' revert: 'r' exit: '0'")
    print("help: 'python chess.py -h'")
    args = parser.parse_args()
    
    board = Board()
    computer_turn = False if board.white_turn else True
    ai_player = None
    if args.ai:
        if args.color == "b" or args.color == "black":
            # TODO rewrite this to go according to current state
            computer_turn = True if board.white_turn else False
    if args.ai == "r" or args.ai == "random":
        ai_player = RandomPlayer(board, False)
    if args.ai == "m" or args.ai == "minmax":
        # TODO here add choice of heuristic as well
        ai_player = MinMaxPlayer(board, computer_turn, material_heuristic,
                                 depth = args.depth)

    moves_input = []
    if args.test:
        with open(args.test) as f:
            for line in f:
                print(line)
                moves_input.append(line.strip())
    
    # TODO refactor this

    print(board) 
    while True:
        if ai_player and ai_player.is_white == board.white_turn:
            # TODO change so AI plays and returns status and move
            move = ai_player.get_ai_move()
            try:
                origin, target, promotion = move
                game_status = board.move_piece(origin, target, promotion)
                print("computer's move")
                print(board)
                if end_game(game_status):
                    break
            except Exception as e:
                print(e)
                continue
        else:
            print("enter move")
            move_input = moves_input.pop(0) if len(moves_input) > 0 else input()
            if move_input == 'r':
                try:
                    board.revert_last_move()
                    #  TODO differnetiate if black or white
                    if ai_player:
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
                else:
                    # TODO return this for any invalid input
                    print("invalid move. try again.")
                    continue
                origin = text_to_coords(start)
                target = text_to_coords(end)
                promotion = text_to_promotion(promote_choice)
                game_status = board.move_piece(origin, target, promotion)
                print(board)
                if end_game(game_status):
                    break
            except MissingPromotionChoice as e:
                promotion = ask_promote(board, moves_input)
                if promotion == None:
                    break
                game_status = board.move_piece(origin, target, promotion)           
                print(board)
                if end_game(game_status):
                    break         
            except ValueError as e:
                print(e)
