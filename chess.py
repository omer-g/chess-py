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


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="path to test file")
    parser.add_argument("-ai", "--ai", help="play against AI: r - random")
    # TODO add argument to choose color
    args = parser.parse_args()

    board = Board()
    print(INTRO)
    print("move: 'e2 e4' or 'a7 a8 Q' revert: 'r' exit: '0'")
    print("help: 'python chess.py -h'\n")
    print(board)

    file_moves = []
    if args.test:
        with open(args.test) as f:
            for line in f:
                print(line)
                file_moves.append(line.strip())
    
    ai_enabled = False
    if args.ai == "r":
        ai_enabled = True
    
    # TODO remove this - take turn only from board itself
    white_turn = True
    computer_turn = False
    # TODO refactor this 
    while True:
        if computer_turn == white_turn and ai_enabled:
            moves = board.generate_moves()
            move = random.choice(moves)
            # move = minmax(depth = 5)
            board.move_piece(move[0], move[1], move[2])
            print("computer's move")
            print(board)
            white_turn = not white_turn
        else:
            print("enter move")
            move_input = file_moves.pop(0) if len(file_moves) > 0 else input()
            if move_input == 'r':
                try:
                    board.revert_last_move()
                    if ai_enabled:
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
                if (move_return == BoardStatus.Checkmate or
                    move_return == BoardStatus.Stalemate
                ):
                    break            
                white_turn = not white_turn
            except MissingPromotionChoice as e:
                promotion = ask_promote(board, file_moves)
                if promotion == None:
                    break
                move_return = board.move_piece(origin, target, promotion)            
                print(board)
                if (move_return == BoardStatus.Checkmate or
                    move_return == BoardStatus.Stalemate
                ):
                    break              
                white_turn = not white_turn

            except ValueError as e:
                print(e)
