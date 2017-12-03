from channels.routing import route
from .consumers import *

channel_routing = [
    route('websocket.connect', ws_connect, path=r"^/web_socket/"),
    route("websocket.receive", websocket_receive, path=r"^/web_socket/"),
    route('websocket.disconnect', ws_disconnect, path=r"^/web_socket/"),
]
