import os
from flask import Flask, current_app, render_template
from flask.ext.bootstrap import Bootstrap

from garnison.web import bp as web_bp
from gachette_web.build_handler import blueprint as build_bp
from gachette_web.stack_handler import blueprint as stack_bp
#from gachette_web.socket_handler import blueprint as websocket_bp
from garnison_api.resources import add_resources
from flask.ext.restful import Api


def create_app(config_file=None, debug=False):
    """
    Factory for the main application.
    """
    app = Flask(__name__)

    # configuration
    app.debug = debug
    if config_file:
        app.config.from_pyfile(config_file)

    # attach Bootstrap plugin
    Bootstrap(app)

    # register blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(build_bp, url_prefix='/build')
    app.register_blueprint(stack_bp, url_prefix='/stack')
    #app.register_blueprint(websocket_bp, url_prefix='/ws')
    #app.register_blueprint(mise-a-feu_bp, url_prefix='/deploy')
    api = add_resources(Api(app))

    return app
