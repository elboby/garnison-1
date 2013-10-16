import datetime
import imp
import json
import os
import redis

import functools

config = os.environ.get('GACHETTE_SETTINGS', './config.rc')
dd = imp.new_module(config)

with open(config) as config_file:
    dd.__file__ = config_file.name
    exec(compile(config_file.read(), config_file.name, 'exec'), dd.__dict__)

class RedisBackend(object):
    """
    Handle redis operations eg. checking, listing, creating...
    """
    def __init__(self, redis_host=None):
        self.redis_host = redis_host if redis_host else dd.REDIS_HOST
        self.redis = redis.Redis(self.redis_host)

        def _set(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # patch redis.set to use pipe if pipe defined in context
                try:
                    assert isinstance(pipe, redis.client.Pipeline)
                    print type(self), "Using redis pipline"
                    pipe.set(*args, **kwargs)
                except NameError:
                    f(*args, **kwargs)
            return wrapper

        # self.redis.original_set = self.redis.set
        self.redis.set = _set(self.redis.set)

    @property
    def domain_defaults(self):
        return dict(
            last_stack_version = "",
            last_deployed_staging = "",
            last_deployed_live = "",
            available_packages = [],
        )

    @property
    def stack_defaults(self):
        return dict(
            meta = {
                "created_by": "Devops Engineer",
                "created_at": datetime.datetime.utcnow().isoformat(),
                "stable": False,
                "deployed_staging_at": "Never",
                "deployed_live_at": "Never",
            },
            packages = {},
        )

    @property
    def build_defaults(self):
        return dict(
            created_by = "Devops Engineer",
            created_at = datetime.datetime.utcnow().isoformat(),
            branch = "",
            commit = "",
        )

    # DOMAINS
    def domain_exists(self, domain):
        val = self.redis.get("domains:%s" % domain)
        return True if val else False

    def create_domain(self, domain):
        if self.domain_exists(domain):
            raise TypeError("Domain '%s' exists" % domain)
        self.redis.set("domains:%s" % domain, json.dumps(self.domain_defaults))

    def get_domain(self, domain):
        domain_ = self.redis.get("domains:%s" % domain)
        return json.loads(domain_) if domain_ else domain_

    def update_domain(self, domain, **kwargs):
        for k, v in kwargs.items():
            assert k in self.domain_defaults, "Key '%s' not allowed" % k
        assert self.domain_exists, "Domain '%s' does not exist" % domain
        d = self.get_domain(domain)
        d.update(kwargs)
        self.redis.set("domains:%s" % domain, json.dumps(d))

    def list_domains(self):
        all_keys = map(lambda k: k.split(":")[1], self.redis.keys("domains:*"))
        return list(set(all_keys))

    # STACKS
    def stack_exists(self, domain, stack):
        val = self.redis.get("domains:%s:stacks:%s" % (domain, stack))
        return True if val else False

    def create_stack(self, domain, stack):
        if self.stack_exists(domain, stack):
            raise TypeError("Stack 'domains:%s:stacks:%s' exists" % (domain, stack))
        if not self.domain_exists(domain):
            raise TypeError("Domain '%s' does not exist" % domain)
        self.redis.set("domains:%s:stacks:%s" % (domain, stack), json.dumps(self.stack_defaults))

    def get_stack(self, domain, stack):
        stack_ = self.redis.get("domains:%s:stacks:%s" % (domain, stack))
        return json.loads(stack_) if stack_ else stack_

    def update_stack(self, domain, stack, **kwargs):
        for k, v in kwargs.items():
            assert k in self.stack_defaults, "Key '%s' not allowed" % k
        assert self.stack_exists(domain, stack), ("Stack 'domains:%s:stacks:%s' does not exist" %
                                                  (domain, stack))
        s = self.get_stack(domain, stack)
        s.update(kwargs)
        self.redis.set("domains:%s:stacks:%s" % (domain, stack), json.dumps(s))

    def list_stacks(self, domain, detail=None):
        if detail:
            keys = self.redis.keys("domains:%s:stacks:*" % domain)
            if not keys:
                return []
            values = self.redis.mget(keys)
            assert len(keys) == len(values)
            stacks = []
            for k, v in zip(keys, values):
                stack_dict = json.loads(v)
                stack_dict["name"] = k.split(":")[3]
                stacks.append(stack_dict)
            sort_key = lambda s: s["meta"]["created_at"]
            return sorted(stacks, key=sort_key, reverse=True)

        return map(lambda k: k.split(":")[3],
                   self.redis.keys("domains:%s:stacks:*" % domain))

    def copy_stack_packages(self, domain=None, source=None, dest=None):
        assert (domain and source and dest), "domain, source, dest are required kwargs"
        assert source != dest, "Source and destination are the same, '%s'" % source
        # TODO check dest stack write protect
        s_stack = self.get_stack(domain, source)
        d_stack = self.get_stack(domain, dest)
        self.update_stack(domain, dest, packages=s_stack["packages"])

    # PACKAGES
    def package_exists(self, package, version):
        val = self.redis.get("packages:%s:%s" % (package, version))
        return True if val else False

    def create_package(self, package, version, pkg_dict):
        if self.package_exists(package, version):
            raise TypeError("Package 'packages:%s' exists" % package)
        self.redis.set("packages:%s:%s" % (package, version), json.dumps(pkg_dict))

    def get_package(self, package, version=None):
        if version is not None:
            package_ = self.redis.get("packages:%s:%s" % (package, version))
            return json.loads(package_) if package_ else package_
        versions = {}
        for key in self.redis.keys("packages:%s:*" % package):
            p = self.redis.get(key)
            v = key.split(":")[2]
            if not p:
                raise AssertionError("Packages '%s', empty?" % key)
            pcontent = json.loads(p)
            # paranoid check
            for deb_dict in pcontent:
                assert deb_dict["version"] == v, "Version mismatch in package: %s" % key
            versions[v] = pcontent
        return versions

    def list_packages(self):
        return list(set(map(lambda k: k.split(":")[1], self.redis.keys("packages:*"))))

    def available_packages(self, domain):
        if not self.domain_exists(domain):
            raise TypeError("Domain 'domains:%s' does not exist" % domain)
        return self.get_domain(domain)["available_packages"]

    def add_stack_package(self, domain, stack, pkg_name, pkg_version):
        if not self.stack_exists(domain, stack):
            raise TypeError("Stack 'domains:%s:stacks:%s' does not exist" % (domain, stack))
        s = self.get_stack(domain, stack)
        s["packages"][pkg_name] = pkg_version
        self.update_stack(domain, stack, packages=s["packages"])

    def get_latest_version(self, package, return_base=None):
        keys = self.redis.keys("packages:%s:*" % package)
        if not keys:
            return ""
        full_version = max(keys).split(":")[2]
        if return_base is None:
            return full_version
        return full_version.split("rev")[0]

    def get_new_base_version(self, package):
        latest = self.get_latest_version(package, return_base=True)
        if not latest:
            return "1"
        return str(1 + int(latest))

    # BUILDS


    # LOCKS
    def lock_exists(self, type_, name):
        val = self.redis.get("locks:%s:%s" % (type_, name))
        return True if val else False

    def create_lock(self, type_, name):
        if self.lock_exists(type_, name):
            raise TypeError("Lock '%s:%s' exists" % (type_, name))
        self.redis.set("locks:%s:%s" % (type_, name), datetime.datetime.utcnow().isoformat())

    def list_locks(self):
        lock_namespace = set(map(lambda k: k.split(":")[1], self.redis.keys("locks:*")))
        locks = {}
        for lock_type in lock_namespace:
            locks[lock_type] = map(lambda k: k.split(":")[2],
                                   self.redis.keys("locks:%s:*" % lock_type))
        return locks

    def delete_lock(self, type_, name):
        if not self.redis.delete("locks:%s:%s" % (type_, name)):
            print "Lock: 'locks:%s:%s' not found" % (type_, name)
            # TODO log inexistent
