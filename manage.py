#!/usr/bin/env python
import os
from flask.ext.script import Server, Manager, Shell

from garnison.main import create_app


# configuration from env var
config_file = os.environ['GACHETTE_SETTINGS']
config_file = os.path.realpath(os.path.expanduser(config_file)) 
print "config_file: ", config_file

# create the main Flask application
app = create_app(config_file=config_file, debug=True)

# Create and configure the Manager
manager = Manager(app)
manager.add_command("runserver", Server(host='0.0.0.0'))

@manager.shell
def make_shell_context():
    "(i)Python shell"
    return dict(app=app)

@manager.command
def dump_config():
    "Pretty print the config"
    for key in sorted(app.config.iterkeys()):
        print "%s: %s" % (key, app.config[key])

if __name__ == "__main__":
    manager.run()