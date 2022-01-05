import aiohttp_cors
import aioredis
import bcrypt
import jwt
import socketio
from aiohttp.web import Application, run_app, Response
from aiohttp.web_exceptions import *
from aiohttp.web_request import Request
from aiohttp.web_response import json_response

import config
from controller.auth import generate_token, is_expired_token, is_valid_token

socketio_server = socketio.AsyncServer(cors_allowed_origins='*')
web_application = Application()
socketio_server.attach(web_application)


# When connect to root url
async def open_web(request: Request):
    with open("static/html/index.html", encoding="utf-8") as f:
        return Response(text=f.read(), content_type="text/html")


# When connect to login url
async def open_login_page(request: Request):
    with open("static/html/login.html", encoding="utf-8") as f:
        return Response(text=f.read(), content_type="text/html")


# Login handler
async def login_handler(request: Request):
    post_body = await request.json()
    user_id = post_body.get("user_id")
    user_password = post_body.get("user_password")

    hashed_password = await redis.get(user_id)
    if user_id is None or user_password is None:
        raise HTTPPaymentRequired()
    elif hashed_password is None:
        raise HTTPUnauthorized()
    is_verified = bcrypt.checkpw(str(user_password).encode("utf-8"), hashed_password)
    if not is_verified:
        return HTTPUnauthorized()
    # When signed ID found
    access_token, refresh_token = await generate_token(redis, user_id)
    token_to_generate = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    return json_response(token_to_generate)


# Login with Token
async def login_with_token(request: Request):
    print(request.headers.get("Authorization"))
    token = str(request.headers.get("Authorization")).split(" ")[1]
    credential_exception = HTTPUnauthorized()
    try:
        if not await is_valid_token(redis, token):
            raise credential_exception
        return HTTPOk()

    except jwt.exceptions.InvalidTokenError:
        raise credential_exception

    # access_token = post_body.get("access_token")
    # refresh_token = post_body.get("refresh_token")
    # if is_expired_token(refresh_token):
    #     payload = jwt.decode(access_token, config.SECRET_KEY, "HS256")
    #     user_id: int = payload.get("user_id")
    #     redis.delete(access_token)
    #     access_token, refresh_token = generate_token(redis, user_id)
    #     token_to_generate = {
    #         "access_token": access_token,
    #         "refresh_token": refresh_token,
    #     }
    #     return json_response(token_to_generate)
    # else:
    #     raise HTTPUnauthorized()


async def signup_handler(request):
    post_body = await request.json()
    user_id = post_body.get("user_id")
    user_password = post_body.get("user_password")
    # Check account exists
    if await redis.get(user_id) is not None:
        return HTTPConflict()
    hashed_password = bcrypt.hashpw(str(user_password).encode('utf-8'), bcrypt.gensalt()).decode()
    await redis.set(user_id, hashed_password)
    if user_id is not None:
        return json_response({"user_id": user_id})
    return HTTPClientError()


async def user_logout(request: Request):
    token = str(request.headers.get("Authorization")).split(" ")[1]
    credential_exception = HTTPUnauthorized()
    try:
        if not await is_valid_token(redis, token):
            raise credential_exception
        payload = jwt.decode(token, config.SECRET_KEY, "HS256")
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credential_exception
        redis.delete(token)
        return HTTPOk()
    except jwt.exceptions.InvalidTokenError:
        raise credential_exception


# 처음 소켓 연결할 때
@socketio_server.on("connect", namespace="/talk")
def connect_server(event_id, data):
    print("connect")


# 채팅을 전송할 때
@socketio_server.on('send_message', namespace='/talk')
async def message(event_id, data):
    print("message received ", data)
    await socketio_server.emit('received_message', {'data': data}, namespace='/talk')


# 소켓 연결을 종료할 때
@socketio_server.on('disconnect', namespace='/talk')
def disconnect(event_id):
    print('disconnect ')


redis = aioredis.from_url("redis://redis:6379")
web_application.router.add_get("/", open_web)
web_application.router.add_get("/login_page", open_login_page)
web_application.router.add_post("/login", login_handler)
web_application.router.add_get("/user", login_with_token)
web_application.router.add_post("/signup", signup_handler)

web_application.router.add_post("/user", login_with_token)
web_application.router.add_static("/static", "static")
cors = aiohttp_cors.setup(web_application, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})


def main():
    run_app(web_application)


if __name__ == '__main__':
    main()
