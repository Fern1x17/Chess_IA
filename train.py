import json
from board import Board
from minimax import Minimax


class Trainer:
    def __init__(self, depth=3, games=20, weight_file="weights.json"):
        self.depth = depth
        self.games = games
        self.weight_file = weight_file
        # cargar pesos o usar iniciales
        try:
            with open(self.weight_file, "r") as f:
                self.weights = json.load(f)
        except FileNotFoundError:
            self.weights = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9}

    def evaluate(self, board):
        """Función de evaluación usando los pesos guardados"""
        score = 0
        for square, piece in board.piece_map().items():
            value = self.weights.get(piece.symbol().upper(), 0)
            if piece.color == board.turn:  # positivo si es turno actual
                score += value
            else:
                score -= value
        return score

    def play_game(self):
        board = Board()
        while not board.is_game_over():
            ai = Minimax(depth=self.depth)
            ai.evaluate = self.evaluate
            move = ai.best_move(board)
            board.push(move)
        return board.result()

    def train(self):
        for i in range(self.games):
            result = self.play_game()
            print(f"Partida {i+1}: {result}")
            # Ajuste de pesos simple: aumentar peones si gana blanca, etc.
            pieces = ["P", "N", "B", "R", "Q"]
            if result == "1-0":
                for p in pieces:
                    self.weights[p] *= 1.01
            elif result == "0-1":
                for p in pieces:
                    self.weights[p] *= 0.99
            elif result == "1/2-1/2":
                for p in pieces:
                    self.weights[p] *= 1.00  
            with open(self.weight_file, "w") as f:
                json.dump(self.weights, f)
                print("Pesos guardados:", self.weights)      


if __name__ == "__main__":
    trainer = Trainer(depth=1, games=100000)
    trainer.train()
