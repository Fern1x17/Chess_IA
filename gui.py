import pygame
import chess
import threading
import sys
import io
import os
import cairosvg
from minimax import Minimax

# ── Layout ────────────────────────────────────────────────────────────────────
SQ = 70                        # pixels per square
BOARD_PX = SQ * 8             # 560
LABEL_W = 24                   # rank/file label area
WIN_W = BOARD_PX + LABEL_W    # 584
WIN_H = BOARD_PX + LABEL_W + 90  # board + file labels + info panel

# ── Colours ───────────────────────────────────────────────────────────────────
C_LIGHT      = (240, 217, 181)
C_DARK       = (181, 136, 99)
C_LIGHT_SEL  = (205, 210, 106)
C_DARK_SEL   = (170, 162, 58)
C_LIGHT_LAST = (207, 185, 132)
C_DARK_LAST  = (164, 117, 68)
C_BG         = (22, 21, 18)
C_PANEL      = (32, 28, 22)
C_TEXT       = (220, 200, 160)
C_DOT        = (100, 180, 80)
C_RING       = (210, 80, 80)
C_BTN        = (160, 110, 50)
C_BTN_HOV    = (200, 145, 75)
C_BTN_TXT    = (255, 245, 220)
C_TITLE      = (255, 230, 140)
C_SUB        = (180, 160, 110)

# ── SVG sprite names ──────────────────────────────────────────────────────────
_SVG_DIR = os.path.join(os.path.dirname(__file__), 'pieces-basic-svg')

_SVG_NAME = {
    (chess.PAWN,   chess.WHITE): 'pawn-w',
    (chess.PAWN,   chess.BLACK): 'pawn-b',
    (chess.KNIGHT, chess.WHITE): 'knight-w',
    (chess.KNIGHT, chess.BLACK): 'knight-b',
    (chess.BISHOP, chess.WHITE): 'bishop-w',
    (chess.BISHOP, chess.BLACK): 'bishop-b',
    (chess.ROOK,   chess.WHITE): 'rook-w',
    (chess.ROOK,   chess.BLACK): 'rook-b',
    (chess.QUEEN,  chess.WHITE): 'queen-w',
    (chess.QUEEN,  chess.BLACK): 'queen-b',
    (chess.KING,   chess.WHITE): 'king-w',
    (chess.KING,   chess.BLACK): 'king-b',
}


# ── Coordinate helpers (player = WHITE at bottom) ─────────────────────────────
def sq_to_screen(sq):
    """Return pixel (x, y) of the top-left corner of the square."""
    file = chess.square_file(sq)
    rank = chess.square_rank(sq)
    x = LABEL_W + file * SQ
    y = (7 - rank) * SQ   # rank 8 at top, rank 1 at bottom
    return x, y


def screen_to_sq(px, py):
    """Return chess square index from pixel position, or None."""
    col = (px - LABEL_W) // SQ
    row = py // SQ
    if not (0 <= col < 8 and 0 <= row < 8):
        return None
    rank = 7 - row
    return chess.square(col, rank)


# ── SVG sprite loader ─────────────────────────────────────────────────────────
_piece_cache = {}

def _load_svg_surf(piece_type, color, size):
    key = (piece_type, color, size)
    if key in _piece_cache:
        return _piece_cache[key]
    name = _SVG_NAME[(piece_type, color)]
    path = os.path.join(_SVG_DIR, f'{name}.svg')
    png_bytes = cairosvg.svg2png(url=path, output_width=size, output_height=size)
    surf = pygame.image.load(io.BytesIO(png_bytes), '.png').convert_alpha()
    _piece_cache[key] = surf
    return surf


def _get_piece_surf(piece, use_unicode=None, piece_font=None, letter_font=None, scale=1.0):
    size = int(SQ * scale)
    return _load_svg_surf(piece.piece_type, piece.color, size)


# ── Board drawing ─────────────────────────────────────────────────────────────
def draw_board(screen, selected_sq, last_move, legal_targets, capture_targets):
    for rank in range(8):
        for file in range(8):
            sq = chess.square(file, rank)
            x = LABEL_W + file * SQ
            y = (7 - rank) * SQ
            light = (rank + file) % 2 == 1

            # Base colour
            if sq == selected_sq:
                colour = C_LIGHT_SEL if light else C_DARK_SEL
            elif last_move and sq in (last_move.from_square, last_move.to_square):
                colour = C_LIGHT_LAST if light else C_DARK_LAST
            else:
                colour = C_LIGHT if light else C_DARK

            pygame.draw.rect(screen, colour, (x, y, SQ, SQ))

    # Rank labels (1–8) on left
    label_font = pygame.font.SysFont('arial', 13, bold=True)
    for rank in range(8):
        y = (7 - rank) * SQ + SQ // 2 - 7
        txt = label_font.render(str(rank + 1), True, C_LIGHT if rank % 2 == 0 else C_DARK)
        screen.blit(txt, (4, y))

    # File labels (a–h) at bottom
    for file in range(8):
        x = LABEL_W + file * SQ + SQ // 2 - 6
        lbl = chr(ord('a') + file)
        light = (file) % 2 == 1
        txt = label_font.render(lbl, True, C_LIGHT if light else C_DARK)
        screen.blit(txt, (x, BOARD_PX + 4))

    # Legal move indicators
    for sq in legal_targets:
        x, y = sq_to_screen(sq)
        cx, cy = x + SQ // 2, y + SQ // 2
        r = SQ // 6
        dot_surf = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        pygame.draw.circle(dot_surf, (*C_DOT, 160), (SQ // 2, SQ // 2), r)
        screen.blit(dot_surf, (x, y))

    for sq in capture_targets:
        x, y = sq_to_screen(sq)
        ring_surf = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*C_RING, 180), (SQ // 2, SQ // 2), SQ // 2 - 4, 6)
        screen.blit(ring_surf, (x, y))


def draw_pieces(screen, board, dragging_sq, drag_pos):
    for sq, piece in board.piece_map().items():
        if sq == dragging_sq:
            continue
        x, y = sq_to_screen(sq)
        surf = _get_piece_surf(piece)
        screen.blit(surf, (x, y))

    # Draw dragged piece on top, centered on mouse
    if dragging_sq is not None:
        piece = board.piece_at(dragging_sq)
        if piece:
            surf = _get_piece_surf(piece, scale=1.08)
            sz = surf.get_width()
            screen.blit(surf, (drag_pos[0] - sz // 2, drag_pos[1] - sz // 2))


# ── Panel drawing ─────────────────────────────────────────────────────────────
def draw_panel(screen, board, status_msg, ai_thinking, fonts):
    panel_y = BOARD_PX + LABEL_W
    pygame.draw.rect(screen, C_PANEL, (0, panel_y, WIN_W, 90))
    pygame.draw.line(screen, (80, 65, 40), (0, panel_y), (WIN_W, panel_y), 2)

    small, med = fonts['small'], fonts['medium']

    # Turn indicator
    if board.is_game_over():
        result = board.result()
        if result == '1-0':
            msg = '¡Ganaste!'
        elif result == '0-1':
            msg = 'La IA gana'
        else:
            msg = 'Tablas'
        turn_txt = med.render(msg, True, C_TITLE)
    else:
        turn = 'Tu turno (Blancas)' if board.turn == chess.WHITE else ('IA pensando…' if ai_thinking else 'IA pensando…')
        turn_txt = med.render(turn, True, C_TEXT)
    screen.blit(turn_txt, (12, panel_y + 10))

    # Status line (last AI move, check, etc.)
    if status_msg:
        st = small.render(status_msg, True, C_SUB)
        screen.blit(st, (12, panel_y + 45))

    # Thinking spinner dots
    if ai_thinking:
        t = pygame.time.get_ticks() // 300 % 4
        dots = '.' * t
        dot_txt = med.render(f'Calculando{dots}', True, C_BTN_HOV)
        screen.blit(dot_txt, (WIN_W - 220, panel_y + 10))


# ── Button helper ──────────────────────────────────────────────────────────────
def draw_button(screen, text, rect, font, hovered):
    colour = C_BTN_HOV if hovered else C_BTN
    pygame.draw.rect(screen, colour, rect, border_radius=10)
    pygame.draw.rect(screen, C_TITLE, rect, 2, border_radius=10)
    txt = font.render(text, True, C_BTN_TXT)
    tr = txt.get_rect(center=rect.center)
    screen.blit(txt, tr)


# ── Welcome screen ────────────────────────────────────────────────────────────
def welcome_screen(screen, clock, fonts):
    btn_rect = pygame.Rect(WIN_W // 2 - 120, WIN_H // 2 + 30, 240, 65)

    # Draw mini board pattern as background
    tile = pygame.Surface((SQ // 2, SQ // 2))

    while True:
        mx, my = pygame.mouse.get_pos()
        hovered = btn_rect.collidepoint(mx, my)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and hovered:
                return  # start game

        screen.fill(C_BG)

        # Subtle chessboard background
        for r in range(16):
            for f in range(16):
                light = (r + f) % 2 == 0
                c = (35, 30, 22) if light else (28, 24, 18)
                pygame.draw.rect(screen, c, (f * SQ // 2, r * SQ // 2, SQ // 2, SQ // 2))

        # Title
        title = fonts['title'].render('AJEDREZ', True, C_TITLE)
        tr = title.get_rect(center=(WIN_W // 2, WIN_H // 2 - 120))
        screen.blit(title, tr)

        sub = fonts['medium'].render('Juega contra la Inteligencia Artificial', True, C_SUB)
        sr = sub.get_rect(center=(WIN_W // 2, WIN_H // 2 - 60))
        screen.blit(sub, sr)

        # Decorative line
        pygame.draw.line(screen, C_BTN, (WIN_W // 2 - 150, WIN_H // 2 - 30),
                         (WIN_W // 2 + 150, WIN_H // 2 - 30), 2)

        draw_button(screen, '▶   JUGAR', btn_rect, fonts['btn'], hovered)

        hint = fonts['small'].render('Juegas con las Blancas', True, C_SUB)
        hr = hint.get_rect(center=(WIN_W // 2, WIN_H // 2 + 120))
        screen.blit(hint, hr)

        pygame.display.flip()
        clock.tick(60)


# ── Game screen ───────────────────────────────────────────────────────────────
def game_screen(screen, clock, fonts):
    board = chess.Board()
    ai = Minimax(depth=4)

    selected_sq = None
    dragging_sq = None
    drag_pos = (0, 0)
    legal_targets = set()
    capture_targets = set()
    last_move = None
    status_msg = ''
    ai_thinking = False
    ai_move_result = [None]

    def run_ai():
        ai_move_result[0] = ai.best_move(board)
        ai_thinking_flag[0] = False

    ai_thinking_flag = [False]

    def start_ai():
        nonlocal ai_thinking
        ai_thinking = True
        ai_thinking_flag[0] = True
        t = threading.Thread(target=run_ai, daemon=True)
        t.start()

    def _update_highlights(sq):
        nonlocal legal_targets, capture_targets
        legal_targets = set()
        capture_targets = set()
        if sq is None:
            return
        piece = board.piece_at(sq)
        if piece is None or piece.color != board.turn:
            return
        for m in board.legal_moves:
            if m.from_square == sq:
                if board.is_capture(m):
                    capture_targets.add(m.to_square)
                else:
                    legal_targets.add(m.to_square)

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()

        # ── AI move applied ────────────────────────────────────────────────
        if ai_thinking and not ai_thinking_flag[0]:
            ai_thinking = False
            move = ai_move_result[0]
            if move and not board.is_game_over():
                san = board.san(move)
                board.push(move)
                last_move = move
                status_msg = f'IA jugó: {san}'
                if board.is_check():
                    status_msg += '  ¡Jaque!'
            ai_move_result[0] = None

        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return  # back to welcome

            # ── Mouse down: pick up piece ──────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if board.is_game_over() or ai_thinking or board.turn != chess.WHITE:
                    continue
                sq = screen_to_sq(mx, my)
                if sq is None:
                    selected_sq = None
                    _update_highlights(None)
                    continue
                piece = board.piece_at(sq)

                # Click on own piece → select / start drag
                if piece and piece.color == chess.WHITE:
                    selected_sq = sq
                    dragging_sq = sq
                    drag_pos = (mx, my)
                    _update_highlights(sq)

                # Click on a highlighted target → move (click-to-move)
                elif selected_sq is not None and sq in (legal_targets | capture_targets):
                    move = chess.Move(selected_sq, sq)
                    # Handle promotion: auto-queen
                    promo_moves = [m for m in board.legal_moves
                                   if m.from_square == selected_sq and m.to_square == sq]
                    if promo_moves:
                        move = promo_moves[0]
                        if move.promotion is None and any(m.promotion for m in promo_moves):
                            move = chess.Move(selected_sq, sq, promotion=chess.QUEEN)
                    if move in board.legal_moves:
                        san = board.san(move)
                        board.push(move)
                        last_move = move
                        status_msg = f'Jugaste: {san}'
                        if board.is_check():
                            status_msg += '  ¡Jaque!'
                        selected_sq = None
                        dragging_sq = None
                        _update_highlights(None)
                        if not board.is_game_over():
                            start_ai()
                else:
                    selected_sq = None
                    dragging_sq = None
                    _update_highlights(None)

            # ── Mouse move: update drag position ───────────────────────────
            if event.type == pygame.MOUSEMOTION and dragging_sq is not None:
                drag_pos = (mx, my)

            # ── Mouse up: drop piece ───────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging_sq is not None:
                target = screen_to_sq(mx, my)
                moved = False
                if target is not None and target != dragging_sq:
                    promo_moves = [m for m in board.legal_moves
                                   if m.from_square == dragging_sq and m.to_square == target]
                    if promo_moves:
                        move = promo_moves[0]
                        if any(m.promotion for m in promo_moves):
                            move = chess.Move(dragging_sq, target, promotion=chess.QUEEN)
                        if move in board.legal_moves:
                            san = board.san(move)
                            board.push(move)
                            last_move = move
                            status_msg = f'Jugaste: {san}'
                            if board.is_check():
                                status_msg += '  ¡Jaque!'
                            selected_sq = None
                            _update_highlights(None)
                            moved = True
                            if not board.is_game_over():
                                start_ai()

                if not moved:
                    # Piece snaps back
                    drag_pos = sq_to_screen(dragging_sq)
                dragging_sq = None

        # ── Draw ──────────────────────────────────────────────────────────
        screen.fill(C_BG)
        draw_board(screen, selected_sq, last_move, legal_targets, capture_targets)
        draw_pieces(screen, board, dragging_sq, drag_pos)
        draw_panel(screen, board, status_msg, ai_thinking, fonts)

        pygame.display.flip()
        clock.tick(60)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption('Ajedrez IA')
    clock = pygame.time.Clock()

    fonts = {
        'title':  pygame.font.SysFont('arial', 62, bold=True),
        'btn':    pygame.font.SysFont('arial', 28, bold=True),
        'medium': pygame.font.SysFont('arial', 20),
        'small':  pygame.font.SysFont('arial', 15),
    }

    while True:
        welcome_screen(screen, clock, fonts)
        _piece_cache.clear()
        game_screen(screen, clock, fonts)


if __name__ == '__main__':
    main()
