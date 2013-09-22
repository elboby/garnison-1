import os
from flask import Flask, current_app, render_template
from flask.ext.bootstrap import Bootstrap

from garnison.web import bp as web_bp
from gachette_web.build_handler import blueprint as build_bp
from gachette_web.stack_handler import blueprint as stack_bp
#from gachette_web.socket_handler import blueprint as websocket_bp

def create_app():
    app = Flask(__name__)

    app.debug = True

    # TODO
    # app.config.from_envvar('GACHETTE_SETTINGS')
    config_file = os.environ.get('GACHETTE_SETTINGS', "")
    print "config_file:", config_file
    if config_file:
        app.config.from_pyfile(config_file)

    print "app.config: ", app.config

    Bootstrap(app)

    app.register_blueprint(web_bp)
    app.register_blueprint(build_bp, url_prefix='/build')
    app.register_blueprint(stack_bp, url_prefix='/stack')
    #app.register_blueprint(websocket_bp, url_prefix='/ws')

    return app
