from flask import Blueprint, jsonify, request, current_app
from fabric.api import settings

from gachette_web.tasks import init_add_package_to_stack_process


blueprint = Blueprint('gachette-web-stack', __name__,)

@blueprint.route('/add/<stack>/', methods=['POST'])
def add_to_stack_call(stack):
    """
    Trebuchet web callback will make a POST HTTP request with a json body that contains:
    <name>, <version>, <file_name> of the package, right after it is built by Trebuchet.

    curl -X POST -H "Content-Type: application/json" -d '{"name": "foo", "version": "0.0.0", "file_name": "foo-0.0.0-all.deb"}' 192.168.0.1:5000/stack/add/123/

    """
    host = current_app.config.get("BUILD_HOST")
    data = request.json
    print "received: " + str(data)

    # async call to add package to stack
    init_add_package_to_stack_process.delay(host, stack, data['name'], data['version'], data['file_name'])

    return jsonify(**data)
