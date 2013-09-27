#!/usr/bin/env python
from fabric.api import settings, env
from celery import Celery
import os
import imp
from redis import Redis

from gachette.working_copy import WorkingCopy
from gachette.stack import Stack

from operator import StackOperatorRedis

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

# get settings
key_filename = None if not hasattr(dd, "BUILD_KEY_FILENAME") else dd.BUILD_KEY_FILENAME
host = dd.BUILD_HOST

def send_notification(data):
    """
    Send notification using Pubsub Redis
    """
    red = Redis(dd.REDIS_HOST, int(dd.REDIS_PORT))
    red.publish("all", ['publish', data])


@celery.task
def init_build_process(name, stack, project, url, branch, app_version, env_version, service_version, path_to_missile=None, webcallback=None):
    """
    stack preparation
    """
    args = ["name", "stack", "project", "url", "branch", "app_version", "env_version", "service_version", "path_to_missile", "webcallback"]
    for arg in args:
        print arg , ": ", locals()[arg]
    with settings(host_string=host, key_filename=key_filename):
        # TODO handle clone
        new_stack = Stack(stack, target_folder="/var/gachette/", operator=StackOperatorRedis(redis_host=dd.REDIS_HOST))
        new_stack.persist()
    send_notification("stack #%s created" % stack)

    # call next step async
    checkout_build_process.delay(name, url, branch, app_version, env_version, service_version, path_to_missile, webcallback)


@celery.task
def checkout_build_process(name, url, branch, app_version, env_version, service_version, path_to_missile=None, webcallback=None):
    """
    Prepare working copy
    """
    args = ["name", "url", "branch", "app_version", "env_version", "service_version", "path_to_missile", "webcallback"]
    for arg in args:
        print arg , ": ", locals()[arg]
    with settings(host_string=host, key_filename=key_filename):
        wc = WorkingCopy(name, base_folder="/var/gachette")
        wc.prepare_environment()
        wc.checkout_working_copy(url=url, branch=branch)
        # TODO retrieve list of package
    send_notification("WorkingCopy #%s updated with %s" % (name, branch))

    # call next step async
    final_build_process.delay(name, app_version, env_version, service_version, path_to_missile, webcallback)


@celery.task
def final_build_process(name, app_version, env_version, service_version, path_to_missile=None, webcallback=None):
    """
    launch build
    """
    args = ["name", "app_version", "env_version", "service_version", "path_to_missile", "webcallback"]
    for arg in args:
        print arg , ": ", locals()[arg]
    with settings(host_string=host, key_filename=key_filename):
        wc = WorkingCopy(name, base_folder="/var/gachette")
        wc.set_version(app=app_version, 
                    env=env_version, 
                    service=service_version)
        wc.build(output_path="/var/gachette/debs", path_to_missile=path_to_missile, webcallback=webcallback)
        send_notification("WorkingCopy #%s build launched" % name)

@celery.task
def init_add_package_to_stack_process(stack, name, version, file_name):
    """
    Add built package to the stack.
    """
    with settings(host_string=host, key_filename=key_filename):
        s = Stack(stack, target_folder="/var/gachette/", operator=StackOperatorRedis(redis_host=dd.REDIS_HOST))
        s.add_package(name, version=version, file_name=file_name)
        send_notification("stack #%s package %s (%s) added" % (stack, name, version))
