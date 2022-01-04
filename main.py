import aiohttp_cors
from aiohttp.web import Application, run_app, Response

import socketio

socketio_server = socketio.AsyncServer(cors_allowed_origins='*')
web_application = Application()
socketio_server.attach(web_application)


async def open_web(request):
    with open("index.html", encoding="utf-8") as f:
        return Response(text=f.read(), content_type="text/html")


@socketio_server.on("connect", namespace="/talk")
def connect_server(event_id, data):
    print("connect")


@socketio_server.on('send_message', namespace='/talk')
async def message(event_id, data):
    print("message received ", data)
    await socketio_server.emit('received_message', {'data': data}, namespace='/talk')


@socketio_server.on('disconnect', namespace='/talk')
def disconnect(event_id):
    print('disconnect ')


web_application.router.add_get("/", open_web)
web_application.router.add_static("/static", "css")
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
