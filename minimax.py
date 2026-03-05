# minimax.py
import chess
import random


class Minimax:
    def __init__(self, depth=2):
        self.depth = depth

    def evaluate(self, board):
        """Valoración muy simple: suma del material"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        score = 0
        for square, piece in board.piece_map().items():
            value = piece_values.get(piece.piece_type, 0)
            center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
            for sq in center_squares:
                piece = board.board.piece_at(sq)
                if piece:
                    if piece.color == board.turn:
                        score += value
                    else:
                        score -= value
        return score

    def minimax(self, board, depth, maximizing_player):
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)

        if maximizing_player:
            max_eval = -float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self.minimax(board, depth-1, False)
                board.pop()
                if eval > max_eval:
                    max_eval = eval
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self.minimax(board, depth-1, True)
                board.pop()
                if eval < min_eval:
                    min_eval = eval
            return min_eval

    def best_move(self, board):
        best_moves = []
        best_eval = -float('inf') if board.turn else float('inf')

        for move in board.legal_moves:
            board.push(move)
            eval = self.minimax(board, self.depth-1, not board.turn)
            board.pop()

            if ((board.turn and eval > best_eval) or
                    (not board.turn and eval < best_eval)):
                best_eval = eval
                best_moves = [move]
            elif eval == best_eval:
                best_moves.append(move)

        return random.choice(best_moves)
