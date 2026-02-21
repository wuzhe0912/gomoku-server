"""Room management: creation, joining, leaving, and cleanup."""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import WebSocket

from app.game import GameState
from app.models import (
    ErrorMsg,
    GameOverMsg,
    GameStartedMsg,
    OpponentDisconnectedMsg,
    PlayerJoinedMsg,
    RoomCreatedMsg,
    StonePlacedMsg,
)


@dataclass
class Player:
    ws: WebSocket
    token: str
    color: str  # "black" | "white"
    connected: bool = True


@dataclass
class Room:
    room_id: str
    players: list[Player] = field(default_factory=list)
    game: GameState = field(default_factory=GameState)
    game_started: bool = False
    turn_timer_task: asyncio.Task | None = field(default=None, repr=False)
    disconnect_tasks: dict[str, asyncio.Task] = field(default_factory=dict, repr=False)

    def get_player_by_token(self, token: str) -> Player | None:
        for p in self.players:
            if p.token == token:
                return p
        return None

    def get_player_by_ws(self, ws: WebSocket) -> Player | None:
        for p in self.players:
            if p.ws is ws:
                return p
        return None

    def get_opponent(self, player: Player) -> Player | None:
        for p in self.players:
            if p is not player:
                return p
        return None

    async def broadcast(self, msg_dict: dict):
        for p in self.players:
            if p.connected:
                try:
                    await p.ws.send_json(msg_dict)
                except Exception:
                    pass

    async def send_to(self, player: Player, msg_dict: dict):
        if player.connected:
            try:
                await player.ws.send_json(msg_dict)
            except Exception:
                pass


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, Room] = {}
        self._ws_to_room: dict[WebSocket, str] = {}

    def _generate_room_id(self) -> str:
        while True:
            room_id = secrets.token_hex(3)  # 6-char hex
            if room_id not in self.rooms:
                return room_id

    async def create_room(self, ws: WebSocket) -> Room:
        room_id = self._generate_room_id()
        room = Room(room_id=room_id)

        token = str(uuid4())
        player = Player(ws=ws, token=token, color="black")
        room.players.append(player)

        self.rooms[room_id] = room
        self._ws_to_room[ws] = room_id

        await ws.send_json(
            RoomCreatedMsg(room_id=room_id, player_token=token, color="black").model_dump()
        )
        return room

    async def join_room(self, ws: WebSocket, room_id: str) -> Room | None:
        room = self.rooms.get(room_id)
        if room is None:
            await ws.send_json(ErrorMsg(message="Room not found").model_dump())
            return None
        if len(room.players) >= 2:
            await ws.send_json(ErrorMsg(message="Room is full").model_dump())
            return None
        if room.game.is_game_over:
            await ws.send_json(ErrorMsg(message="Game already ended").model_dump())
            return None

        token = str(uuid4())
        player = Player(ws=ws, token=token, color="white")
        room.players.append(player)
        self._ws_to_room[ws] = room_id

        # Notify the new player
        await ws.send_json(
            RoomCreatedMsg(room_id=room_id, player_token=token, color="white").model_dump()
        )

        # Notify the first player that someone joined
        host = room.players[0]
        await room.send_to(host, PlayerJoinedMsg(color="white").model_dump())

        # Start the game
        room.game_started = True
        for p in room.players:
            await room.send_to(p, GameStartedMsg(your_color=p.color).model_dump())

        return room

    async def place_stone(self, ws: WebSocket, row: int, col: int):
        room = self.get_room_for_ws(ws)
        if room is None:
            await ws.send_json(ErrorMsg(message="Not in a room").model_dump())
            return
        if not room.game_started:
            await ws.send_json(ErrorMsg(message="Game not started yet").model_dump())
            return

        player = room.get_player_by_ws(ws)
        if player is None:
            return

        error = room.game.validate_move(row, col, player.color)
        if error:
            await ws.send_json(ErrorMsg(message=error).model_dump())
            return

        game_ended = room.game.place_stone(row, col, player.color)

        if game_ended:
            next_turn = None
        else:
            next_turn = room.game.current_turn

        await room.broadcast(
            StonePlacedMsg(row=row, col=col, color=player.color, next_turn=next_turn).model_dump()
        )

        if game_ended:
            if room.game.winner:
                reason = "five_in_row"
            else:
                reason = "draw"
            await room.broadcast(
                GameOverMsg(winner=room.game.winner, reason=reason).model_dump()
            )
            # Cancel turn timer if active
            if room.turn_timer_task and not room.turn_timer_task.done():
                room.turn_timer_task.cancel()

    async def handle_disconnect(self, ws: WebSocket):
        room_id = self._ws_to_room.pop(ws, None)
        if room_id is None:
            return

        room = self.rooms.get(room_id)
        if room is None:
            return

        player = room.get_player_by_ws(ws)
        if player is None:
            return

        player.connected = False
        opponent = room.get_opponent(player)

        if opponent and opponent.connected:
            await room.send_to(opponent, OpponentDisconnectedMsg().model_dump())

            # Schedule room cleanup after 60 seconds if player doesn't reconnect
            async def cleanup_after_timeout():
                await asyncio.sleep(60)
                if not player.connected:
                    if not room.game.is_game_over and room.game_started:
                        room.game.is_game_over = True
                        room.game.winner = opponent.color
                        await room.broadcast(
                            GameOverMsg(winner=opponent.color, reason="disconnect").model_dump()
                        )
                    self._cleanup_room(room_id)

            task = asyncio.create_task(cleanup_after_timeout())
            room.disconnect_tasks[player.token] = task
        else:
            self._cleanup_room(room_id)

    def _cleanup_room(self, room_id: str):
        room = self.rooms.pop(room_id, None)
        if room is None:
            return
        if room.turn_timer_task and not room.turn_timer_task.done():
            room.turn_timer_task.cancel()
        for task in room.disconnect_tasks.values():
            if not task.done():
                task.cancel()

    def get_room_for_ws(self, ws: WebSocket) -> Room | None:
        room_id = self._ws_to_room.get(ws)
        if room_id is None:
            return None
        return self.rooms.get(room_id)


room_manager = RoomManager()
