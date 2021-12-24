from aiohttp.web import Application, run_app
from aiohttp.web import get
from controller.socket import chatting_socket_controller


async def init_webapp() -> Application:
    # Create Web application object
    application = Application()

    # Declare dict to include socket object
    application["websockets"] = {}

    # Close all web sockets when turn off server
    application.on_shutdown.append(close_webapp)

    # Endpoint that client can request
    application.add_routes([get("/talk", handler=chatting_socket_controller)])
    return application


async def close_webapp(app: Application):
    for web_socket in app.get("websocket").values():
        web_socket.close()
    app.get("websockets").clear()


def main():
    application = init_webapp()
    run_app(application)


if __name__ == '__main__':
    main()
