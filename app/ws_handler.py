"""WebSocket endpoint and message routing."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models import ErrorMsg, parse_client_message

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
            # Message routing will be added in subsequent commits
            await ws.send_json(ErrorMsg(message=f"Handler for '{msg.type}' not yet implemented").model_dump())
    except WebSocketDisconnect:
        pass
