import datetime
import json

import redis

from exceptions import *
from garnison_api.backends import RedisBackend

class StackOperatorRedis(object):
    """
    Process action related to the stack. Redis backed up.
    """

    def __init__(self, redis_host=None):
        self.server = redis.Redis(redis_host if redis_host else "127.0.0.1")

    def get_last_stack_version(self, domain):
        return RedisBackend().get_domain(domain)["last_stack_version"]

    def set_last_stack_version(self, domain, version):
        RedisBackend().update_domain(domain, last_stack_version=version)

    def initialize_stack(self, stack, **kwargs):
        """
        Initiate stack in redis. Create all meta information fields.
        """
        # Run create & update in pipeline (transaction)
        with RedisBackend().redis.pipeline() as pipe:
            RedisBackend().create_stack(stack.domain, stack.version)
            RedisBackend().update_stack(stack.domain, stack.version, **kwargs)
            pipe.execute()

    def setup_packages(self, stack, from_stack=False, use_latest_packages=False):
        """
        If ``use_latest_packages`` use latest package versions
        Elif ``from_stack`` copy packages from source stack
        """
        if use_latest_packages:
            raise NotImplemented("Not yet available")
        if not from_stack:
            return

        if from_stack and from_stack.domain != stack.domain:
            errstr = "Stack domains do not match. New: %s Source: %s" % (stack.domain, from_stack.domain)
            raise TypeError(errstr)

        # Paranoid check
        backend = RedisBackend()
        assert backend.stack_exists(stack.domain, stack.version), "New stack doesn't exist"
        assert backend.stack_exists(from_stack.domain, from_stack.version), "Old stack doesn't exist"
        source_stack = backend.get_stack(from_stack.domain, from_stack.version)
        backend.update_stack(stack.domain, stack.version, packages=source["packages"])

        # available_packages_json = self.server.get("%s:available_packages" % stack.domain)
        # available_packages = json.loads(available_packages_json) if available_packages_json else []

        # stack_package_key = "%s:stack:%s:package" % (stack.domain, stack.version)

        # for package in available_packages:
        #     if from_stack:  # get the version from source stack
        #         source_stack_package_key = ("%s:stack:%s:package:%s" %
        #                                     (from_stack.domain, from_stack.version, package))
        #         pkg = json.loads(self.server.get(source_stack_package_key))
        #         version = pkg["version"]
        #     else:  # get latest version
        #         package_key = "package:%s:last_version" % package
        #         version = self.server.get(package_key)
        #         if version == None:
        #             raise PackageNotBuiltException("%s has never been built" % package)
        #     pkg = {
        #         "name": package, "version": version, "file_name": "%s-%s.deb" % (package, version)
        #     }

        #     self.server.set("%s:%s" % (stack_package_key, package), json.dumps(pkg))


    def test_stack_exists(self, domain, stack):
        """
        Check if stack exists in redis.
        """
        return RedisBackend().stack_exists(domain, stack)

    def add_stack_package(self, stack, pkg_name, pkg_version, pkg_filename):
        """
        Registers a built package in the stack.
        """
        
        pkg = {
            "name": pkg_name, "version": pkg_version,
            "filename": pkg_filename
        }
        RedisBackend().add_stack_package(stack.domain, stack.version, pkg)

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
