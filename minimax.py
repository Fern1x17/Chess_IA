# minimax.py — Negamax with alpha-beta, PSTs, move ordering, quiescence, TT
import chess
import random

PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:   20000,
}

# Piece-square tables in python-chess order: index = square (a1=0, h8=63)
# For white: use sq directly.  For black: mirror with sq ^ 56.

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
KING_MID_TABLE = [
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]
KING_END_TABLE = [
    -50,-30,-30,-30,-30,-30,-30,-50,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -50,-40,-30,-20,-20,-30,-40,-50,
]

_PST_MID = {
    chess.PAWN:   PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK:   ROOK_TABLE,
    chess.QUEEN:  QUEEN_TABLE,
    chess.KING:   KING_MID_TABLE,
}

# Transposition table flags
_EXACT = 0
_LOWER = 1  # fail-high (beta cutoff)
_UPPER = 2  # fail-low

_TT_MAX = 1_000_000
_tt: dict = {}


def _is_endgame(board):
    queens = sum(1 for p in board.piece_map().values() if p.piece_type == chess.QUEEN)
    heavy = sum(1 for p in board.piece_map().values()
                if p.piece_type in (chess.ROOK, chess.QUEEN))
    return queens == 0 or heavy <= 2


def _pst(piece, sq, endgame):
    idx = sq ^ 56 if piece.color == chess.BLACK else sq
    if piece.piece_type == chess.KING:
        return KING_END_TABLE[idx] if endgame else KING_MID_TABLE[idx]
    return _PST_MID[piece.piece_type][idx]


def evaluate(board):
    """Static eval from the current player's perspective (negamax convention)."""
    if board.is_checkmate():
        return -100_000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    endgame = _is_endgame(board)
    score = 0
    for sq, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type] + _pst(piece, sq, endgame)
        score += val if piece.color == board.turn else -val

    score += len(list(board.legal_moves)) * 4
    return score


def _mvv_lva(board, move):
    victim = board.piece_at(move.to_square)
    attacker = board.piece_at(move.from_square)
    if victim is None:
        return 0
    vv = PIECE_VALUES[victim.piece_type]
    av = PIECE_VALUES[attacker.piece_type] if attacker else 100
    return vv * 10 - av


def _order(board):
    def key(m):
        s = 0
        if board.is_capture(m):
            s += 10_000 + _mvv_lva(board, m)
        if m.promotion:
            s += PIECE_VALUES.get(m.promotion, 0) + 5_000
        tf, tr = chess.square_file(m.to_square), chess.square_rank(m.to_square)
        if 2 <= tf <= 5 and 2 <= tr <= 5:
            s += 20
        return s
    return sorted(board.legal_moves, key=key, reverse=True)


def _quiescence(board, alpha, beta, depth=5):
    stand = evaluate(board)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    if depth == 0:
        return alpha

    captures = sorted(
        (m for m in board.legal_moves if board.is_capture(m)),
        key=lambda m: _mvv_lva(board, m),
        reverse=True,
    )
    for move in captures:
        board.push(move)
        score = -_quiescence(board, -beta, -alpha, depth - 1)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


import time as _time

_deadline = [0.0]
_abort = [False]
_nodes = [0]


def _negamax(board, depth, alpha, beta):
    if _abort[0]:
        return 0

    alpha_orig = alpha
    key = board._transposition_key()

    # Transposition table lookup
    entry = _tt.get(key)
    if entry and entry[0] >= depth:
        stored_depth, score, flag = entry
        if flag == _EXACT:
            return score
        if flag == _LOWER:
            alpha = max(alpha, score)
        elif flag == _UPPER:
            beta = min(beta, score)
        if alpha >= beta:
            return score

    if board.is_game_over():
        return -100_000 - depth if board.is_checkmate() else 0

    if depth == 0:
        return _quiescence(board, alpha, beta)

    _nodes[0] += 1
    if _nodes[0] & 0xFF == 0 and _time.time() >= _deadline[0]:
        _abort[0] = True
        return 0

    best = -float('inf')
    for move in _order(board):
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha)
        board.pop()
        if _abort[0]:
            break
        best = max(best, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break

    # Store in TT only for complete (non-aborted) searches
    if not _abort[0] and len(_tt) < _TT_MAX:
        flag = _EXACT if alpha_orig < best < beta else (_LOWER if best >= beta else _UPPER)
        _tt[key] = (depth, best, flag)

    return best


class Minimax:
    def __init__(self, depth=6, time_limit=2.0):
        self.max_depth = depth
        self.time_limit = time_limit

    def best_move(self, board):
        moves = _order(board)
        if not moves:
            return None

        _deadline[0] = _time.time() + self.time_limit
        best_move_so_far = moves[0]

        for depth in range(1, self.max_depth + 1):
            _abort[0] = False
            _nodes[0] = 0
            candidate = None
            best_val = -float('inf')

            for move in moves:
                # Time check at root level between root moves
                if _time.time() >= _deadline[0]:
                    _abort[0] = True
                    break
                board.push(move)
                val = -_negamax(board, depth - 1, -float('inf'), float('inf'))
                board.pop()
                if _abort[0]:
                    break
                if val > best_val:
                    best_val = val
                    candidate = move

            # Only update best if this depth completed without timeout
            if not _abort[0] and candidate is not None:
                best_move_so_far = candidate
                moves = [candidate] + [m for m in moves if m != candidate]

            if _abort[0] or _time.time() >= _deadline[0]:
                break

        return best_move_so_far

    def evaluate(self, board):
        return evaluate(board)
