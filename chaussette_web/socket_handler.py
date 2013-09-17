#!/usr/bin/env python

# http://sontek.net/blog/detail/pycon-sprints-part-1-the-realtime-web-with-gevent-socket-io-redis-and-django

import json
from flask import Blueprint, request, current_app, render_template

from redis import Redis
from gevent.greenlet import Greenlet


blueprint = Blueprint('gachette-web-socket', __name__,)


def _sub_listener(ws, chan, redis_con):
    """
    This is the method that will block and listen
    for new messages to be published to redis, since
    we are using coroutines this method can block on
    listen() without interrupting the rest of the site
    """
    red = Redis(redis_con)
    p = red.pubsub()
    p.subscribe(chan)
    print "subscribed"

    for i in p.listen():
        print "listened: " + str(i)
        ws.send(json.dumps({"message": i}))


@blueprint.route('/')
def home():
    return render_template('socket.html')


@blueprint.route('/send/<data>')
def send(data):
    red = Redis(current_app.config.get("REDIS_HOST"))
    red.publish("all", ['publish', data])
    return "publishing: " + data

 
@blueprint.route('/connect')
def connect():
    print "ws: " + str(request.environ.get('wsgi.websocket'))
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        while True:
            message = ws.receive()
            
            if message == 'subscribe':
                print "subscribing"
                g = Greenlet.spawn(_sub_listener, ws, "all", current_app.config.get("REDIS_HOST"))
            else:
                print "message: ", message
                message = "hello i just got: " + message + "<br/>\n"
                ws.send(message)

    return "nope"
