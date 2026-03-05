from board import Board
from minimax import Minimax


board = Board()
ai = Minimax(depth=2)


while not board.is_game_over():
    board.display()
    move_input = input("Tu jugada (en formato SAN, ej. e4, Nf3): ")
    try:
        # move = board.parse_san(move_input)
        board.move(move_input)
    except ValueError:
        print("Movimiento inválido, intenta otra vez")
        continue

    ai_move = ai.best_move(board)
    ai_move_san = board.san(ai_move)
    board.push(ai_move)
    print(f"IA juega: {ai_move_san}")
print("Game over!")
