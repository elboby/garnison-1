#!/usr/bin/env python
from flask.ext.script import Server, Manager, Shell

from garnison.main import create_app

app = create_app()

def _make_context():
    return dict(app=app)

manager = Manager(app)
manager.add_command("runserver", Server(host='0.0.0.0'))
manager.add_command("shell", Shell(make_context=_make_context))

@manager.command
def hello():
    print "hello"

if __name__ == "__main__":
    manager.run()