#!/usr/bin/env python
from garnison.main import app

HOST = "0.0.0.0"
PORT = 5000

if __name__ == '__main__':
    app.run(host=HOST)

    # from geventwebsocket.handler import WebSocketHandler
    # from gevent.pywsgi import WSGIServer

    # # use gevent to patch the standard lib to get async support
    # from gevent import monkey
    # monkey.patch_all()

    # http_server = WSGIServer((HOST,PORT), app, handler_class=WebSocketHandler)
    # http_server.serve_forever()