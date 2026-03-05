import chess


class Board:
    def __init__(self):
        self.board = chess.Board()

    def move(self, move_san):
        """Mueve usando notación SAN (ej. 'e4', 'Nf3')"""
        self.board.push_san(move_san)

    def push(self, move):
        """Empuja un objeto Move de python-chess"""
        self.board.push(move)

    def pop(self):
        """Deshace el último movimiento"""
        self.board.pop()

    def display(self):
        """Imprime el tablero"""
        print(self.board)

    @property
    def turn(self):
        return self.board.turn

    @property
    def legal_moves(self):
        return list(self.board.legal_moves)

    def is_game_over(self):
        return self.board.is_game_over()

    def piece_map(self):
        return self.board.piece_map()

    def san(self, move):
        """Convierte un objeto Move a notación SAN"""
        return self.board.san(move)

    def result(self):
        """Devuelve el resultado de la partida: '1-0', '0-1' o '1/2-1/2'"""
        return self.board.result()
