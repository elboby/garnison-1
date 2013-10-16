import json

import flask
from flask import Flask, request
from flask.ext.restful import Resource, abort, reqparse

from gachette_web.tasks import package_build_process

from .backends import RedisBackend

PROJECTS_DATA = {
    'test_config': {
        'repo': 'git@github.com:ops-hero/test_config.git',
        'path_to_missile': None
    },
    'test_application': {
        'repo': 'git@github.com:ops-hero/test_application.git',
        'path_to_missile': None
    },
}

class BaseResource(Resource):
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.reqparse = reqparse.RequestParser()

class DomainList(BaseResource):
    def get(self):
        return {"domains": RedisBackend().list_domains()}

class Domain(BaseResource):
    def get(self, domain):
        domain = RedisBackend().get_domain(domain)
        return domain if domain else abort(404)

    def put(self, domain):  # TODO maybe POST?
        try:
            RedisBackend().create_domain(domain)
            return {"status": 201, "message": "Created"}
        except TypeError as e:
            abort(409, status=409, message="Conflict", info=str(e))

class StackList(BaseResource):
    def get(self, domain):
        self.reqparse.add_argument("detail", type=str)
        args = self.reqparse.parse_args()
        if args["detail"]:
            stacks = RedisBackend().list_stacks(domain, detail=True)
        else:
            stacks = RedisBackend().list_stacks(domain)
        return {"stacks": stacks}

class Stack(BaseResource):
    def get(self, domain, stack):
        stack = RedisBackend().get_stack(domain, stack)
        return stack if stack else abort(404, status=404, info="Stack not found")

    def put(self, domain, stack):
        self.reqparse.add_argument("copy_packages_from", type=str)
        args = self.reqparse.parse_args()
        source = args["copy_packages_from"]
        try:
            RedisBackend().create_stack(domain, stack)
        except TypeError as e:
            print e
            abort(409, status=409, message="Conflict", info=str(e))
        if source:
            try:
                RedisBackend().copy_stack_packages(domain=domain, source=source, dest=stack)
            except AssertionError as e:
                print e
                abort(400, status=400, message=repr(e))
        return {"status": 201, "message": "Created"}

class Build(BaseResource):
    def put(self, project):
        self.reqparse.add_argument("branch", type=str, default="master")
        self.reqparse.add_argument("domain", type=str)
        self.reqparse.add_argument("stack", type=str)
        args = self.reqparse.parse_args()
        branch, domain, stack = args["branch"], args["domain"], args["stack"]
        
        if domain and stack:
            if not RedisBackend().stack_exists(domain, stack):
                abort(404, status=404, message="Not Found", info="Domain and/or stack does not exist")
        if project not in PROJECTS_DATA:
            abort(404, status=404, message="Not Found", info="Project not found")
        try:
            RedisBackend().create_lock("packages", project)
        except TypeError as e:
            print e
            abort(409, status=409, message="Conflict", info="Build in progress")
        from multiprocessing import Process
        p = Process(target=package_build_process,
                    args=(project, PROJECTS_DATA[project]["repo"], branch),
                    kwargs={"path_to_missile": PROJECTS_DATA[project]["path_to_missile"],
                            "domain": domain, "stack":stack},
                   )
        p.start()
        return {"status": 201, "message": "Created"}
        # package_build_process.delay(project, PROJECTS_DATA[project]["repo"],
        #                       "master",
        #                       path_to_missile=PROJECTS_DATA[project]["path_to_missile"],
        #                       domain=domain, stack=stack)

    def get(self, project):
        print project

class PackageList(BaseResource):
    def get(self):
        return {"packages": RedisBackend().list_packages()}

class Package(BaseResource):
    def get(self, package):
        self.reqparse.add_argument("version", type=str)
        args = self.reqparse.parse_args()
        version = args["version"]
        package = RedisBackend().get_package(package, version=version)
        if not package:
            abort(404, status=404, message="Not Found", info="Package not found")
        return package if not version else {version: package}

class LockList(BaseResource):

    def get(self):
        return {"locks": RedisBackend().list_locks()}

    def delete(self):
        self.reqparse.add_argument("type", type=str)
        self.reqparse.add_argument("name", type=str)
        args = self.reqparse.parse_args()
        type_, name = args["type"], args["name"]
        RedisBackend().delete_lock(type_, name)
        return flask.Response(status=204)


RESOURCES = [
    (DomainList, "/api/domains/"),
    (Domain, "/api/domains/<string:domain>"),
    (StackList, "/api/domains/<string:domain>/stacks/"),
    (Stack, "/api/domains/<string:domain>/stacks/<string:stack>"),
    (Build, "/api/builds/<string:project>"),
    (PackageList, "/api/packages/"),
    (Package, "/api/packages/<string:package>"),
    (LockList, "/api/locks/"),
]

def add_resources(api):
    for resource in RESOURCES:
        api.add_resource(*resource)

