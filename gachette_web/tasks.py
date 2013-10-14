#!/usr/bin/env python
from fabric.api import settings, env
from celery import Celery
import os
import sys
import imp
from redis import Redis
from StringIO import StringIO

from gachette.lib.working_copy import WorkingCopy
from gachette.lib.stack import Stack

from operator import StackOperatorRedis
from garnison_api.backends import RedisBackend

# allow the usage of ssh config file by fabric
env.use_ssh_config = True
env.forward_agent = True
env.warn_only = True
# env.echo_stdin = False
env.always_use_pty = False

import pprint
pp = pprint.PrettyPrinter(indent=2)

pp.pprint(env)

# load config from file via environ variable
config = os.environ.get('GACHETTE_SETTINGS', './config.rc')
dd = imp.new_module('config')

with open(config) as config_file:
    dd.__file__ = config_file.name
    exec(compile(config_file.read(), config_file.name, 'exec'), dd.__dict__)

celery = Celery()
celery.add_defaults(dd)

# get settings
key_filename = None if not hasattr(dd, "BUILD_KEY_FILENAME") else dd.BUILD_KEY_FILENAME
host = dd.BUILD_HOST

class StdinMock(StringIO):
    """Replacement to patch sys.stdin to use fabric within celery task"""
    def fileno(self):
        return 0

    def read(self, *args):
        return 0

def send_notification(data):
    """
    Send notification using Pubsub Redis
    """
    red = Redis(dd.REDIS_HOST, int(dd.REDIS_PORT))
    red.publish("all", ['publish', data])

@celery.task
def package_build_process(name, url, branch, pkg_version, path_to_missile=None,
                          domain=None, stack=None):
    """
    Prepare working copy, checkout working copy, build
    """
    args = ["name", "url", "branch", "pkg_version", "path_to_missile"]
    for arg in args:
        print arg , ": ", locals()[arg]

    sys.stdin = StdinMock()

    
    with settings(host_string=host, key_filename=key_filename):
        wc = WorkingCopy(name, base_folder="/var/gachette")
        wc.prepare_environment()
        # TODO get commit from checkout_working_copy
        wc.checkout_working_copy(url=url, branch=branch)
        send_notification("WorkingCopy #%s updated with %s" % (name, branch))
        wc.set_version(pkg_version)
        result = wc.build(output_path="/var/gachette/debs", path_to_missile=path_to_missile)
        RedisBackend().delete_lock("packages", name)
        send_notification("WorkingCopy #%s build launched" % name)
        # TODO retrieve list of package

        pp.pprint(result)
    if domain is not None and stack is not None:
        for deb_dict in result:
            add_package_to_stack_process(domain, stack, deb_dict["name"],
                                         deb_dict["version"], deb_dict["file_name"])

@celery.task
def add_package_to_stack_process(domain, stack, name, version, file_name):
    """
    Add built package to the stack.
    """
    with settings(host_string=host, key_filename=key_filename):
        s = Stack(domain, stack, meta_path="/var/gachette/", operator=StackOperatorRedis(redis_host=dd.REDIS_HOST))
        s.add_package(name, version=version, file_name=file_name)
        send_notification("domain:stack #%s:%s package %s (%s) added" % (domain, stack, name, version))
