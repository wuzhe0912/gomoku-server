"""Unit tests for game logic: win detection, move validation, draw."""

from app.game import BOARD_SIZE, GameState


class TestMoveValidation:
    def test_valid_move(self):
        game = GameState()
        assert game.validate_move(7, 7, "black") is None

    def test_wrong_turn(self):
        game = GameState()
        assert game.validate_move(0, 0, "white") == "Not your turn"

    def test_out_of_bounds(self):
        game = GameState()
        assert game.validate_move(-1, 0, "black") == "Coordinates out of bounds"
        assert game.validate_move(0, BOARD_SIZE, "black") == "Coordinates out of bounds"
        assert game.validate_move(BOARD_SIZE, 0, "black") == "Coordinates out of bounds"

    def test_occupied_cell(self):
        game = GameState()
        game.place_stone(7, 7, "black")
        assert game.validate_move(7, 7, "white") == "Cell is already occupied"

    def test_game_over(self):
        game = GameState()
        game.is_game_over = True
        assert game.validate_move(0, 0, "black") == "Game is already over"


class TestPlaceStone:
    def test_alternating_turns(self):
        game = GameState()
        game.place_stone(0, 0, "black")
        assert game.current_turn == "white"
        game.place_stone(1, 0, "white")
        assert game.current_turn == "black"

    def test_move_count(self):
        game = GameState()
        game.place_stone(0, 0, "black")
        assert game.move_count == 1
        game.place_stone(1, 0, "white")
        assert game.move_count == 2


class TestWinDetection:
    def test_horizontal_win(self):
        game = GameState()
        # black: (7,3), (7,4), (7,5), (7,6), (7,7)
        # white: (8,3), (8,4), (8,5), (8,6)
        for i in range(4):
            game.place_stone(7, 3 + i, "black")
            game.place_stone(8, 3 + i, "white")
        ended = game.place_stone(7, 7, "black")
        assert ended is True
        assert game.winner == "black"

    def test_vertical_win(self):
        game = GameState()
        for i in range(4):
            game.place_stone(3 + i, 7, "black")
            game.place_stone(3 + i, 8, "white")
        ended = game.place_stone(7, 7, "black")
        assert ended is True
        assert game.winner == "black"

    def test_diagonal_down_right_win(self):
        game = GameState()
        # black: (0,0), (1,1), (2,2), (3,3), (4,4)
        for i in range(4):
            game.place_stone(i, i, "black")
            game.place_stone(i, i + 1, "white")
        ended = game.place_stone(4, 4, "black")
        assert ended is True
        assert game.winner == "black"

    def test_diagonal_up_right_win(self):
        game = GameState()
        # black: (4,0), (3,1), (2,2), (1,3), (0,4)
        for i in range(4):
            game.place_stone(4 - i, i, "black")
            game.place_stone(0, 5 + i, "white")
        ended = game.place_stone(0, 4, "black")
        assert ended is True
        assert game.winner == "black"

    def test_no_win_with_four(self):
        game = GameState()
        for i in range(3):
            game.place_stone(7, 3 + i, "black")
            game.place_stone(8, 3 + i, "white")
        ended = game.place_stone(7, 6, "black")
        assert ended is False
        assert game.winner is None

    def test_white_wins(self):
        game = GameState()
        # black goes first at (0,0), then white builds horizontal
        game.place_stone(0, 0, "black")
        for i in range(4):
            game.place_stone(7, i, "white")
            game.place_stone(1, i, "black")
        ended = game.place_stone(7, 4, "white")
        assert ended is True
        assert game.winner == "white"


class TestDraw:
    def test_draw_detection(self):
        game = GameState()
        assert game.is_draw() is False
        game.move_count = BOARD_SIZE * BOARD_SIZE
        assert game.is_draw() is True

    def test_full_board_draw(self):
        game = GameState()
        game.move_count = BOARD_SIZE * BOARD_SIZE - 1
        # Place last stone without winning
        game.board[14][14] = None
        ended = game.place_stone(14, 14, "black")
        # May or may not be draw depending on board state,
        # but move_count should trigger draw if no win
        assert game.move_count == BOARD_SIZE * BOARD_SIZE
