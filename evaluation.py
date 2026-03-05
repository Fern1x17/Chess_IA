piece_values = {
    "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0
}


def evaluate(board):
    score = 0
    for square in board.board.piece_map().values():
        score += piece_values.get(square.symbol().upper(), 0)
    return score
