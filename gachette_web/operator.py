import datetime
import json

import redis

from exceptions import *

class StackOperatorRedis(object):
    """
    Process action related to the stack. Redis backed up.
    """

    def __init__(self, redis_host=None):
        self.server = redis.Redis(redis_host if redis_host else "127.0.0.1")

    def get_last_stack_version(self, domain):
        key = "%s:last_stack_version" % domain
        version = self.server.get(key)
        if version is None:
            version = "1"
            self.server.set(key, version)
        return version

    def set_last_stack_version(self, domain, version):
        key = "%s:last_stack_version" % domain
        self.server.set(key, version)

    def default_stack_meta(self, override):
        defaults = {
            "created_by": "Devops Engineer",
            "created_at": datetime.datetime.utcnow(),
            "stable": False,
            "deployed_staging_at": "Never",
            "deployed_live_at": "Never",
        }
        # TODO check against extra keys?
        defaults.update(override)
        return defaults

    def initialize_stack(self, stack, **kwargs):
        """
        Initiate stack in redis. Create all meta information fields.
        """
        stack_meta_key = "%s:stack:%s:meta" % (stack.domain, stack.version)
        for key, value in self.default_stack_meta(kwargs).items():
            self.server.set("%s:%s" % (stack_meta_key, key), value)

    def setup_packages(self, stack, from_stack=None):
        """
        If not given id, use last_stack_version to copy packages.

        1. if old_stack defined - copy all package keys to new stack
        2. if old_stack not define - get list of packages from domain:available_packages, iterate over them
            for each one get value from domain:<package_name>:last_version
        """

        if from_stack and from_stack.domain != stack.domain:
            errstr = "Stack domains do not match. New: %s Source: %s" % (stack.domain, from_stack.domain)
            raise TypeError(errstr)

        available_packages_json = self.server.get("%s:available_packages" % stack.domain)
        available_packages = json.loads(available_packages_json) if available_packages_json else []

        stack_package_key = "%s:stack:%s:package" % (stack.domain, stack.version)

        for package in available_packages:
            if from_stack:  # get the version from source stack
                source_stack_package_key = ("%s:stack:%s:package:%s" %
                                            (from_stack.domain, from_stack.version, package))
                pkg = json.loads(self.server.get(source_stack_package_key))
                version = pkg["version"]
            else:  # get latest version
                package_key = "package:%s:last_version" % package
                version = self.server.get(package_key)
                if version == None:
                    raise PackageNotBuiltException("%s has never been built" % package)
            pkg = {
                "name": package, "version": version, "file_name": "%s-%s.deb" % (package, version)
            }

            self.server.set("%s:%s" % (stack_package_key, package), json.dumps(pkg))


    def test_stack_exists(self, domain, stack_version):
        """
        Check if stack exists in redis.
        """
        stack_meta_key = "%s:stack:%s:meta*" % (domain, version)
        keys = self.server.keys(stack_meta_key)
        return True if keys else False

    def add_stack_package(self, stack, package_name, package_version, domain=None):
        """
        Registers a built package in the stack.
        """
        # assert (self.test_stack_exists(domain, stack.version),
        #         "Stack '%s' does not exist" % stack.version)
        
        pkg = {
            "name": package_name, "version": package_version,
            "file_name": "%s-%s.deb" % (package_name, package_version)
        }

        # add to stack
        self.server.set("%s:stack:%s:package:%s" % (domain, stack.version, package_name),
                        json.dumps(pkg))

    def add_reference_package(self, name, version, file_name):
        """
        This was used to create a reference file that contained the package file_name
        """
        pass

    def copy_old_stack(self):
        pass

    def persist_stack(self, stack):
        self.initialize_stack(stack)
        self.setup_packages(stack)
