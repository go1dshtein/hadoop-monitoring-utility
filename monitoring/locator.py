import logging
import os
import re

import yaml

from monitoring.config import get_default_locator_config

logger = logging.getLogger(__name__)


class Locator(object):
    def exits(self):
        raise NotImplementedError('abstract method is called')

    def endpoint(self):
        raise NotImplementedError('abstract method is called')


class DummyLocator(Locator):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.is_exist = True

    def endpoint(self):
        return 'dummy://'

    def exists(self):
        return self.is_exist


class HttpServiceLocator(Locator):
    def __init__(self, host="localhost", port=80):
        self.url = "http://%s:%d" % (host, int(port))

    def exists(self):
        import requests

        try:
            response = requests.head(self.url)
            return response.status_code < 400 or \
                response.status_code == 405
        except requests.exceptions.ConnectionError:
            return False

    def endpoint(self):
        return self.url


class ProcessLocator(Locator):
    processes = None

    def __init__(self, pattern=".*?"):
        self.pattern = pattern
        self.pid = None
        self.user = None

    def endpoint(self):
        if self.pid is not None and self.user is not None:
            return "process://%s@%d" % (self.user, self.pid)

    def exists(self):
        for cmdline, pid, username in self.get_processes():
            if re.match(self.pattern, cmdline, re.S | re.M):
                self.pid = pid
                self.user = username
                return True
        return False

    def get_processes(self):
        import psutil

        if ProcessLocator.processes is not None:
            return ProcessLocator.processes

        processes = []
        for proc in psutil.process_iter():
            try:
                cmdline = " ".join(proc.cmdline)
                processes.append((cmdline, proc.pid, proc.username))
            except psutil.AccessDenied, e:
                logger.debug("psutil: denied: %s", e)
            except psutil.Error, e:
                logger.debug("psutil: %s", e)

        ProcessLocator.processes = processes
        return ProcessLocator.processes


class ServiceLocator(object):
    INSTANCE = None

    def __new__(cls, *args, **kwargs):
        if ServiceLocator.INSTANCE is None:
            ServiceLocator.INSTANCE = \
                super(ServiceLocator, cls).__new__(cls, *args, **kwargs)
        return ServiceLocator.INSTANCE

    def __init__(self):
        self.locators = {}

    def add(self, service_name, service_locator):
        if not isinstance(service_locator, Locator):
            raise TypeError('service_locator should be instance of Locator')

        self.locators[service_name] = service_locator

    def exists(self):
        for name, locator in self.locators.items():
            if locator.exists():
                logger.info("%s found", name)
                yield name

    def endpoint(self, name):
        return self.locators[name].endpoint()

    def load_config(self, filename=None, **kwargs):
        if filename is None:
            filename = get_default_locator_config()
        logger.debug("loading from %s", filename)
        config = self.read_config(filename)
        for name, value in config.items():
            klass, args = self.get_class_and_args(value, kwargs)
            logger.debug("loading: %s: %s(%s)", name, klass, args)
            self.add(name, klass(**args))

    def read_config(self, filename):
        with open(filename) as h:
            config = h.read()
        return yaml.load(config)

    def get_class_and_args(self, args, updates):
        for key, value in updates.items():
            if key in args:
                args[key] = value
        klass = globals()[args["class"]]
        del args["class"]
        return klass, args
