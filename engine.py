from evaluation import evaluate


def minimax(board, depth, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate(board) 
    if maximizing_player:
        max_eval = -float('inf')
        for move in board.get_legal_moves():
            board.move(move)
            eval = minimax(board, depth-1, False)
            board.undo_move()  # si implementas undo
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.get_legal_moves():
            board.move(move)
            eval = minimax(board, depth-1, True)
            board.undo_move()
            min_eval = min(min_eval, eval)
        return min_eval
