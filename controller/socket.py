from aiohttp import WSMessage, WSMsgType
from aiohttp.web_request import Request
from aiohttp.web_ws import WebSocketResponse
from random import randint


async def chatting_socket_controller(request: Request) -> WebSocketResponse:
    current_websocket = WebSocketResponse(autoping=True, heartbeat=50)
    websocket_is_ready = current_websocket.can_prepare(request)

    # Check websocket can prepare request
    if not websocket_is_ready:
        await current_websocket.close()
    await current_websocket.prepare(request)

    # Change state to connecting
    user_id = f"user_{randint(0, 100)}"
    await current_websocket.send_json({'state': 'try to connect', 'user': user_id})

    # Check duplicate user
    if request.app.get("websockets").get(user_id):
        await current_websocket.close()
    else:
        request.app.get("websockets")[user_id] = current_websocket
        # Broadcast join new user
        for websocket in request.get("websockets").values():  # type: WebSocketResponse
            await websocket.send_json({'state': 'join new user', 'user': user_id})

    # When get request from socket
    try:
        async for message in current_websocket:  # type: WSMessage
            if isinstance(message, WSMessage) and message.type == WSMsgType.text:
                body = message.json()
                await current_websocket.send_json({
                    "state": "send message", "success": True, "message": body.get("message")
                 })
                for websocket in request.get("websockets").values():  # type: WebSocketResponse
                    await websocket.send_json({
                        "state": "send message", "sender": user_id, "message": body.get("message")
                    })
    finally:
        request.app.get("websockets").pop(user_id)

    if current_websocket.closed:
        for websocket in request.get("websockets").values():  # type: WebSocketResponse
            await websocket.send_json({"state": "exit", "user": user_id, "normal_disconnect": True})
    else:
        for websocket in request.get("websockets").values():  # type: WebSocketResponse
            await websocket.send_json({"state": "exit", "user": user_id, "normal_disconnect": False})
    return current_websocket
