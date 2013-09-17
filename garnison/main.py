import os
from flask import Flask, current_app, render_template
from flask.ext.bootstrap import Bootstrap

from gachette_web.build_handler import blueprint as build_bp
from gachette_web.stack_handler import blueprint as stack_bp
#from gachette_web.socket_handler import blueprint as websocket_bp

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

app.register_blueprint(build_bp, url_prefix='/build')
app.register_blueprint(stack_bp, url_prefix='/stack')
#app.register_blueprint(websocket_bp, url_prefix='/ws')


@app.route('/')
def home():
    """
    Test. Return status of the builds.
    """
    print "toto"
    for rule in current_app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        print rule.endpoint

    return render_template('index.html')