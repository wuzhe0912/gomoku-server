"""Tests for room lifecycle: creation, joining, leaving."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.room import RoomManager


def make_mock_ws():
    """Create a mock WebSocket that tracks sent messages."""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestRoomCreation:
    @pytest.mark.asyncio
    async def test_create_room(self):
        manager = RoomManager()
        ws = make_mock_ws()
        room = await manager.create_room(ws)

        assert room is not None
        assert len(room.room_id) == 6
        assert len(room.players) == 1
        assert room.players[0].color == "black"
        assert room.room_id in manager.rooms

        # Verify room_created message was sent
        ws.send_json.assert_called_once()
        msg = ws.send_json.call_args[0][0]
        assert msg["type"] == "room_created"
        assert msg["color"] == "black"
        assert "player_token" in msg

    @pytest.mark.asyncio
    async def test_create_multiple_rooms(self):
        manager = RoomManager()
        ws1, ws2 = make_mock_ws(), make_mock_ws()
        room1 = await manager.create_room(ws1)
        room2 = await manager.create_room(ws2)
        assert room1.room_id != room2.room_id
        assert len(manager.rooms) == 2


class TestRoomJoining:
    @pytest.mark.asyncio
    async def test_join_room(self):
        manager = RoomManager()
        ws1, ws2 = make_mock_ws(), make_mock_ws()
        room = await manager.create_room(ws1)

        await manager.join_room(ws2, room.room_id)

        assert len(room.players) == 2
        assert room.players[1].color == "white"
        assert room.game_started is True

    @pytest.mark.asyncio
    async def test_join_nonexistent_room(self):
        manager = RoomManager()
        ws = make_mock_ws()
        result = await manager.join_room(ws, "nonexistent")
        assert result is None
        ws.send_json.assert_called_once()
        msg = ws.send_json.call_args[0][0]
        assert msg["type"] == "error"
        assert "not found" in msg["message"].lower()

    @pytest.mark.asyncio
    async def test_join_full_room(self):
        manager = RoomManager()
        ws1, ws2, ws3 = make_mock_ws(), make_mock_ws(), make_mock_ws()
        room = await manager.create_room(ws1)
        await manager.join_room(ws2, room.room_id)

        result = await manager.join_room(ws3, room.room_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_game_started_broadcast(self):
        manager = RoomManager()
        ws1, ws2 = make_mock_ws(), make_mock_ws()
        room = await manager.create_room(ws1)
        await manager.join_room(ws2, room.room_id)

        # ws1 should receive: room_created, player_joined, game_started
        assert ws1.send_json.call_count == 3
        msgs = [call[0][0] for call in ws1.send_json.call_args_list]
        types = [m["type"] for m in msgs]
        assert "room_created" in types
        assert "player_joined" in types
        assert "game_started" in types

        # ws2 should receive: room_created, game_started
        assert ws2.send_json.call_count == 2


class TestRoomLeaving:
    @pytest.mark.asyncio
    async def test_disconnect_solo_player_cleans_room(self):
        manager = RoomManager()
        ws = make_mock_ws()
        room = await manager.create_room(ws)
        room_id = room.room_id

        await manager.handle_disconnect(ws)
        assert room_id not in manager.rooms

    @pytest.mark.asyncio
    async def test_disconnect_notifies_opponent(self):
        manager = RoomManager()
        ws1, ws2 = make_mock_ws(), make_mock_ws()
        room = await manager.create_room(ws1)
        await manager.join_room(ws2, room.room_id)
        ws2.send_json.reset_mock()

        await manager.handle_disconnect(ws1)

        # ws2 should receive opponent_disconnected
        ws2.send_json.assert_called()
        last_msg = ws2.send_json.call_args[0][0]
        assert last_msg["type"] == "opponent_disconnected"
