"""WebSocket endpoint and message routing."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models import (
    CreateRoomMsg,
    ErrorMsg,
    JoinRoomMsg,
    LeaveRoomMsg,
    parse_client_message,
)
from app.room import room_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            msg = parse_client_message(data)
            if msg is None:
                await ws.send_json(ErrorMsg(message="Unknown or invalid message").model_dump())
                continue

            if isinstance(msg, CreateRoomMsg):
                await room_manager.create_room(ws)

            elif isinstance(msg, JoinRoomMsg):
                await room_manager.join_room(ws, msg.room_id)

            elif isinstance(msg, LeaveRoomMsg):
                await room_manager.handle_disconnect(ws)

            else:
                await ws.send_json(
                    ErrorMsg(message=f"Handler for '{msg.type}' not yet implemented").model_dump()
                )
    except WebSocketDisconnect:
        await room_manager.handle_disconnect(ws)
