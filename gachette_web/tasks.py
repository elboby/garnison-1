#!/usr/bin/env python
from fabric.api import settings, env
from celery import Celery
import os
import imp
from redis import Redis

from gachette.working_copy import WorkingCopy
from gachette.stack import Stack

# allow the usage of ssh config file by fabric
env.use_ssh_config = True
env.forward_agent = True

# load config from file via environ variable
config = os.environ.get('GACHETTE_SETTINGS', './config.rc')
dd = imp.new_module('config')

with open(config) as config_file:
    dd.__file__ = config_file.name
    exec(compile(config_file.read(), config_file.name, 'exec'), dd.__dict__)

celery = Celery()
celery.add_defaults(dd)


def send_notification(data):
    """
    Send notification using Pubsub Redis
    """
    red = Redis(dd.REDIS_HOST, int(dd.REDIS_PORT))
    red.publish("all", ['publish', data])


@celery.task
def init_build_process(host, name, stack, project, url, branch, app_version, env_version, service_version, path_to_missile=None, webcallback=None):
    """
    stack preparation
    """
    with settings(host_string=host):
        # TODO handle clone
        new_stack = Stack(stack)
        new_stack.persist()
    send_notification("stack #%s created" % stack)

    # call next step async
    checkout_build_process.delay(host, name, url, branch, app_version, env_version, service_version, path_to_missile, webcallback)


@celery.task
def checkout_build_process(host, name, url, branch, app_version, env_version, service_version, path_to_missile=None, webcallback=None):
    """
    Prepare working copy
    """
    with settings(host_string=host):
        wc = WorkingCopy(name)
        wc.prepare_environment()
        wc.checkout_working_copy(url, branch)
        # TODO retrieve list of package
    send_notification("WorkingCopy #%s updated with %s" % (name, branch))

    # call next step async
    final_build_process.delay(host, name, app_version, env_version, service_version, path_to_missile, webcallback)


@celery.task
def final_build_process(host, name, app_version, env_version, service_version, path_to_missile=None, webcallback=None):
    """
    launch build
    """
    with settings(host_string=host):
        wc = WorkingCopy(name)
        wc.set_version(app=app_version, 
                    env=env_version, 
                    service=service_version)
        wc.build(path_to_missile, webcallback)
        send_notification("WorkingCopy #%s build launched" % name)

@celery.task
def init_add_package_to_stack_process(host, stack, name, version, file_name):
    """
    Add built package to the stack.
    """
    with settings(host_string=host):
        s = Stack(stack)
        s.add_package(name, version, file_name)
        send_notification("stack #%s package %s (%s) added" % (stack, name, version))