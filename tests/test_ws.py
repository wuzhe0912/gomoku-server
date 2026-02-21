"""WebSocket integration tests using FastAPI TestClient."""

import pytest
from starlette.testclient import TestClient

from app.main import app


class TestWebSocketIntegration:
    def test_health_endpoint(self):
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok"}

    def test_websocket_connect(self):
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.send_json({"type": "create_room"})
                data = ws.receive_json()
                assert data["type"] == "room_created"
                assert data["color"] == "black"
                assert len(data["room_id"]) == 6

    def test_invalid_message(self):
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.send_json({"type": "unknown_type"})
                data = ws.receive_json()
                assert data["type"] == "error"

    def test_full_game_flow(self):
        """Two players create, join, and play until someone wins."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws1:
                # Player 1 creates room
                ws1.send_json({"type": "create_room"})
                msg1 = ws1.receive_json()
                assert msg1["type"] == "room_created"
                room_id = msg1["room_id"]

                with client.websocket_connect("/ws") as ws2:
                    # Player 2 joins
                    ws2.send_json({"type": "join_room", "room_id": room_id})
                    msg2 = ws2.receive_json()
                    assert msg2["type"] == "room_created"
                    assert msg2["color"] == "white"

                    # Player 1 receives player_joined + game_started
                    p1_joined = ws1.receive_json()
                    assert p1_joined["type"] == "player_joined"
                    p1_started = ws1.receive_json()
                    assert p1_started["type"] == "game_started"
                    assert p1_started["your_color"] == "black"

                    # Player 2 receives game_started
                    p2_started = ws2.receive_json()
                    assert p2_started["type"] == "game_started"
                    assert p2_started["your_color"] == "white"

                    # Play moves: black wins with horizontal line
                    # Black: (7,0), (7,1), (7,2), (7,3), (7,4)
                    # White: (8,0), (8,1), (8,2), (8,3)
                    for i in range(4):
                        # Black's move
                        ws1.send_json({"type": "place_stone", "row": 7, "col": i})
                        s1 = ws1.receive_json()
                        assert s1["type"] == "stone_placed"
                        assert s1["color"] == "black"
                        s2 = ws2.receive_json()
                        assert s2["type"] == "stone_placed"

                        # White's move
                        ws2.send_json({"type": "place_stone", "row": 8, "col": i})
                        s1 = ws1.receive_json()
                        assert s1["type"] == "stone_placed"
                        assert s1["color"] == "white"
                        s2 = ws2.receive_json()
                        assert s2["type"] == "stone_placed"

                    # Black's winning move
                    ws1.send_json({"type": "place_stone", "row": 7, "col": 4})
                    s1 = ws1.receive_json()
                    assert s1["type"] == "stone_placed"
                    assert s1["color"] == "black"

                    # Game over for player 1
                    go1 = ws1.receive_json()
                    assert go1["type"] == "game_over"
                    assert go1["winner"] == "black"
                    assert go1["reason"] == "five_in_row"

                    # Player 2 also receives stone_placed + game_over
                    s2 = ws2.receive_json()
                    assert s2["type"] == "stone_placed"
                    go2 = ws2.receive_json()
                    assert go2["type"] == "game_over"
                    assert go2["winner"] == "black"

    def test_wrong_turn_rejected(self):
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws1:
                ws1.send_json({"type": "create_room"})
                msg = ws1.receive_json()
                room_id = msg["room_id"]

                with client.websocket_connect("/ws") as ws2:
                    ws2.send_json({"type": "join_room", "room_id": room_id})
                    ws2.receive_json()  # room_created
                    ws1.receive_json()  # player_joined
                    ws1.receive_json()  # game_started
                    ws2.receive_json()  # game_started

                    # White tries to move first — should fail
                    ws2.send_json({"type": "place_stone", "row": 7, "col": 7})
                    err = ws2.receive_json()
                    assert err["type"] == "error"
                    assert "not your turn" in err["message"].lower()

    def test_join_nonexistent_room(self):
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.send_json({"type": "join_room", "room_id": "bad123"})
                data = ws.receive_json()
                assert data["type"] == "error"
                assert "not found" in data["message"].lower()
