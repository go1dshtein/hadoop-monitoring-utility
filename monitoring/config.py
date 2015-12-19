import yaml
import os
from collections import namedtuple


def make_config(data):
    base = namedtuple('Base', ('oid', 'name'))
    logging = namedtuple('Logging', ('filename', 'level'))
    locator = namedtuple(
        'Locator', ('filename', 'service_map'))
    schemas = namedtuple('Schemas', ('directory',))
    config = namedtuple('Config', ('base', 'logging', 'locator', 'schemas'))

    base = base(data.get('base', {}).get('oid', 'hadoop'),
                data.get('base', {}).get('name', 'hadoop'))
    logging = logging(
        data.get('logging', {}).get('filename'),
        data.get('logging', {}).get('level', 'INFO'))
    locator = locator(
        data.get('locator', {}).get('filename', get_default_locator_config()),
        data.get('locator', {}).get('service_map'))
    schemas = schemas(
        data.get('schemas', {}).get('directory', get_default_schemas_dir()))

    return config(base, logging, locator, schemas)


def load_config(filename):
    if filename is None:
        filename = find_config()

    if filename is None:
        return make_config({})
    if not os.path.exists(filename):
        return make_config({})
    with open(filename) as h:
        return make_config(yaml.load(h.read()))


def get_config_variants():
    variants = [
        os.path.join(os.getcwd(), '.hadoop-monitoring.yaml'),
        os.path.join(os.path.expanduser('~'), '.hadoop-monitoring.yaml'),
        '/etc/hadoop-monitoring.yaml',
    ]
    return variants


def get_default_locator_config():
    return os.path.join(
        os.path.dirname(__file__), 'data', 'locator.yaml')


def get_default_schemas_dir():
    return os.path.join(
        os.path.dirname(__file__), 'data', 'schema')


def get_default_templates_dir():
    return os.path.join(
        os.path.dirname(__file__), 'data', 'subagent')


def find_config():
    for varaint in get_config_variants():
        if os.path.isfile(varaint):
            return varaint
    return None
