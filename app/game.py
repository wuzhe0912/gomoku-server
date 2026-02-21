"""Game logic: board state, move validation, and win detection."""

from __future__ import annotations

BOARD_SIZE = 15

# Four directions: horizontal, vertical, diagonal ↘, diagonal ↗
DIRECTIONS = [
    (0, 1),
    (1, 0),
    (1, 1),
    (1, -1),
]


class GameState:
    def __init__(self):
        self.board: list[list[str | None]] = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_turn: str = "black"
        self.move_count: int = 0
        self.is_game_over: bool = False
        self.winner: str | None = None

    def validate_move(self, row: int, col: int, color: str) -> str | None:
        """Return an error message if the move is invalid, or None if valid."""
        if self.is_game_over:
            return "Game is already over"
        if color != self.current_turn:
            return "Not your turn"
        if row < 0 or row >= BOARD_SIZE or col < 0 or col >= BOARD_SIZE:
            return "Coordinates out of bounds"
        if self.board[row][col] is not None:
            return "Cell is already occupied"
        return None

    def place_stone(self, row: int, col: int, color: str) -> bool:
        """Place a stone and check for win/draw. Returns True if game ends."""
        self.board[row][col] = color
        self.move_count += 1

        if self.check_win(row, col):
            self.is_game_over = True
            self.winner = color
            return True

        if self.is_draw():
            self.is_game_over = True
            self.winner = None
            return True

        # Switch turn
        self.current_turn = "white" if color == "black" else "black"
        return False

    def check_win(self, row: int, col: int) -> bool:
        """Check if the last move at (row, col) creates five-in-a-row."""
        color = self.board[row][col]
        if color is None:
            return False

        for dr, dc in DIRECTIONS:
            count = 1

            # Extend in positive direction
            for i in range(1, 5):
                r, c = row + dr * i, col + dc * i
                if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                    break
                if self.board[r][c] != color:
                    break
                count += 1

            # Extend in negative direction
            for i in range(1, 5):
                r, c = row - dr * i, col - dc * i
                if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                    break
                if self.board[r][c] != color:
                    break
                count += 1

            if count >= 5:
                return True

        return False

    def is_draw(self) -> bool:
        return self.move_count >= BOARD_SIZE * BOARD_SIZE
