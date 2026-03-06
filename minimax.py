# minimax.py
import chess
import random


class Minimax:
    def __init__(self, depth=2):
        self.depth = depth

    def evaluate(self, board):
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        score = 0

        for square, piece in board.piece_map().items():
            value = piece_values[piece.piece_type]

            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value

        # bonus por control del centro
        center = [chess.D4, chess.D5, chess.E4, chess.E5]

        for sq in center:
            piece = board.piece_at(sq)
            if piece:
                if piece.color == chess.WHITE:
                    score += 20
                else:
                    score -= 20                 
        if board.turn == chess.WHITE:
            score += len(list(board.legal_moves))
        else:
            score -= len(list(board.legal_moves))

        return score

    def minimax(self, board, depth, alpha, beta, maximizing_player):

        if depth == 0 or board.is_game_over():
            return self.evaluate(board)

        if maximizing_player:
            max_eval = -float('inf')

            for move in board.legal_moves:
                board.push(move)

                eval = self.minimax(board, depth-1, alpha, beta, False)

                board.pop()

                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)

                if beta <= alpha:
                    break

            return max_eval

        else:
            min_eval = float('inf')

            for move in board.legal_moves:
                board.push(move)

                eval = self.minimax(board, depth-1, alpha, beta, True)

                board.pop()

                min_eval = min(min_eval, eval)
                beta = min(beta, eval)

                if beta <= alpha:
                    break

            return min_eval

    def best_move(self, board):
        # Aleatoriedad en los primeros movimientos para romper simetría
        if board.fullmove_number < 4:
            return random.choice(list(board.legal_moves))

        best_moves = []
        turn = board.turn
        best_eval = -float('inf') if turn == chess.WHITE else float('inf')

        for move in board.legal_moves:
            board.push(move)

            # usar turno original para maximizer
            eval = self.minimax(
                board,
                self.depth - 1,
                -float('inf'),
                float('inf'),
                maximizing_player=(turn == chess.WHITE)
            )

            board.pop()

            if turn == chess.WHITE:
                if eval > best_eval:
                    best_eval = eval
                    best_moves = [move]
                elif eval == best_eval:
                    best_moves.append(move)
            else:
                if eval < best_eval:
                    best_eval = eval
                    best_moves = [move]
                elif eval == best_eval:
                    best_moves.append(move)

        # fallback si no hay movimientos (por si eval falla)
        if not best_moves:
            best_moves = list(board.legal_moves)

        return random.choice(best_moves)
