"""Pydantic models for WebSocket message protocol."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Client → Server
# ---------------------------------------------------------------------------

class CreateRoomMsg(BaseModel):
    type: Literal["create_room"] = "create_room"


class JoinRoomMsg(BaseModel):
    type: Literal["join_room"] = "join_room"
    room_id: str


class PlaceStoneMsg(BaseModel):
    type: Literal["place_stone"] = "place_stone"
    row: int
    col: int


class LeaveRoomMsg(BaseModel):
    type: Literal["leave_room"] = "leave_room"


class ReconnectMsg(BaseModel):
    type: Literal["reconnect"] = "reconnect"
    room_id: str
    player_token: str


ClientMessage = CreateRoomMsg | JoinRoomMsg | PlaceStoneMsg | LeaveRoomMsg | ReconnectMsg


# ---------------------------------------------------------------------------
# Server → Client
# ---------------------------------------------------------------------------

class RoomCreatedMsg(BaseModel):
    type: Literal["room_created"] = "room_created"
    room_id: str
    player_token: str
    color: str


class PlayerJoinedMsg(BaseModel):
    type: Literal["player_joined"] = "player_joined"
    color: str


class GameStartedMsg(BaseModel):
    type: Literal["game_started"] = "game_started"
    your_color: str


class StonePlacedMsg(BaseModel):
    type: Literal["stone_placed"] = "stone_placed"
    row: int
    col: int
    color: str
    next_turn: str | None


class GameOverMsg(BaseModel):
    type: Literal["game_over"] = "game_over"
    winner: str | None
    reason: str  # "five_in_row" | "timeout" | "disconnect" | "draw"


class StateSyncMsg(BaseModel):
    type: Literal["state_sync"] = "state_sync"
    board: list[list[str | None]]
    current_turn: str
    move_count: int
    your_color: str
    timer_remaining: float


class TurnTimerMsg(BaseModel):
    type: Literal["turn_timer"] = "turn_timer"
    remaining: float


class OpponentDisconnectedMsg(BaseModel):
    type: Literal["opponent_disconnected"] = "opponent_disconnected"


class OpponentReconnectedMsg(BaseModel):
    type: Literal["opponent_reconnected"] = "opponent_reconnected"


class ErrorMsg(BaseModel):
    type: Literal["error"] = "error"
    message: str


def parse_client_message(data: dict) -> ClientMessage | None:
    """Parse a raw dict into a typed client message, or None if invalid."""
    msg_type = data.get("type")
    mapping: dict[str, type[BaseModel]] = {
        "create_room": CreateRoomMsg,
        "join_room": JoinRoomMsg,
        "place_stone": PlaceStoneMsg,
        "leave_room": LeaveRoomMsg,
        "reconnect": ReconnectMsg,
    }
    model = mapping.get(msg_type)  # type: ignore[arg-type]
    if model is None:
        return None
    try:
        return model.model_validate(data)  # type: ignore[return-value]
    except Exception:
        return None
