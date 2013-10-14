import os
from flask import Flask, current_app, render_template
from flask.ext.bootstrap import Bootstrap

from garnison.web import bp as web_bp
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
    api = add_resources(Api(app))

    return app
