import collections
import fnmatch
import logging
import os
import yaml

from monitoring.collector import Collector
from monitoring.config import get_default_templates_dir
from monitoring.formatter import HumanOutputFormatter, SubagentOutputFormatter
from monitoring.formatter import MIBOutputFormatter
from monitoring.locator import ServiceLocator
from monitoring.schema import Schema
from monitoring.utils import get_snmp_name

logger = logging.getLogger(__name__)


class CollectorService:
    def __init__(self, host, locator_config=None):
        self.host = host
        self.locator = ServiceLocator()
        self.locator.load_config(locator_config, host=host)
        self.formatters = {
            'human': HumanOutputFormatter(),
            'subagent': SubagentOutputFormatter(),
        }

    def collect(self, oid, name, schema_dir=None):
        metrics = {}
        for schema_name in self.locator.exists():
            schema = Schema.load_schema(schema_name, schema_dir=schema_dir)
            if schema is None:
                continue
            logger.info('collecting data: %s', schema_name)
            collector = Collector(self.locator.endpoint(schema_name), schema)
            metrics.update(collector.collect(oid, name))
        return metrics

    def output(self, metrics, pattern=None, format=None):
        if pattern is None:
            pattern = '*'
        return self.formatters[format].output(metrics, pattern)

    def check_services(self, metrics, service_map, name):
        with open(service_map) as handler:
            services = yaml.load(handler.read()).get(self.host)
        if not services:
            return
        for service in services:
            if not fnmatch.filter(metrics.keys(), '%s.%s.*' % (name, service)):
                logger.warn('seems service %s is unavailable on host %s',
                            get_snmp_name('%s.%s' % (name, service)),
                            self.host)


class MIBGeneratorService:
    def __init__(self, templatedir=None):
        if templatedir is None:
            templatedir = get_default_templates_dir()
        self.templatedir = templatedir

    def generate(self, oid, name):
        objects = collections.OrderedDict()
        for schemaname in Schema.get_available_schemas():
            schema = Schema.load_schema(schemaname)
            objects.update(schema.scan(oid, name))
        return objects

    def output(self, directory, objects):
        formatter = MIBOutputFormatter(self.templatedir)
        formatter.output(objects, directory)
