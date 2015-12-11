import logging
import yaml
import os
import glob
import re
import binascii

from monitoring.utils import get_snmp_name
from monitoring.config import get_default_schemas_dir

logger = logging.getLogger(__name__)


class Schema:
    schema_dir = os.path.join(os.path.dirname(__file__), 'data', 'schema')
    function_pattern = re.compile(
        '(\w+)\(\s*(((\w+)\s*=\s*(.*?),?)+)\s*\)', re.U | re.S)

    def __init__(self, schema):
        self.schema = schema
        self.request_executor = (lambda x, y: None)

    def set_request_executor(self, executor):
        assert callable(executor)
        self.request_executor = executor

    def scan(self, oid, name):
        try:
            return self.recursive_scan(oid, name, self.schema, {}, {})
        except KeyError, e:
            raise KeyError('invalid schema, key error: %s' % e.message)

    def recursive_scan(self, oid, name, node, data, result):
        oid = self.get_oid(oid, node)
        name = self.get_name(name, node)
        logger.debug('oid: %s, name: %s: keys: %s', oid, name, node.keys())

        if 'requests' in node:
            result = self.scan_requests_node(
                oid, name, node['requests'], data, result)
        elif 'resources' in node:
            result = self.scan_resources_node(
                oid, name, node['resources'], data, result)
        elif 'path' in node:
            result[name] = self.get_leaf(oid, name, node, data)
        elif 'table' in node:
            result = self.scan_table_node(
                oid, name, node['table'], data, result)
        return result

    def scan_requests_node(self, oid, name, node, data, result):
        for request in node:
            data = self.request_executor(request['query'],
                                         request.get('endpoint'))
            result = self.recursive_scan(oid, name, request, data, result)
        return result

    def scan_resources_node(self, oid, name, node, data, result):
        for resource in node:
            result = self.recursive_scan(oid, name, resource, data, result)
        return result

    def scan_table_node(self, oid, name, node, data, result):
        fields = node['fields']
        index_field = self.get_table_index_field(oid, name, fields)
        values = self.get_value(data, node['path']) or [None] * len(fields)
        for value in values:
            index = self.get_value(value, index_field['path'])
            for field in fields:
                field_oid = self.get_oid(oid, field)
                field_name = self.get_name(name, field)
                if index is not None:
                    field_oid += '.' + str(index)
                    field_name += '.' + str(index)
                result[field_name] = self.get_leaf(
                    field_oid, field_name, field, value)
        return result

    def get_table_index_field(self, oid, name, fields):
        index_field = None
        for field in fields:
            if field['name'] == 'index':
                index_field = field
        if index_field is None:
            raise KeyError('undefined index field in table %s' % name)
        return index_field

    def get_oid(self, oid, node):
        if 'oid' in node:
            oid = '.'.join([oid, str(node.get('oid'))])
        return oid

    def get_name(self, name, node):
        if 'name' in node:
            name = '.'.join([name, node.get('name')])
        return name

    def get_leaf(self, oid, name, node, data):
        leaf = {}
        leaf['value'] = self.get_value(data, node['path'])
        leaf['type'] = node.get('type', 'OCTET STRING')
        leaf['unit'] = node.get('unit', '')
        leaf['description'] = node.get('description')
        leaf['name'] = name
        leaf['oid'] = oid
        leaf['snmp'] = get_snmp_name(name)
        return leaf

    def get_value(self, data, address):
        if address is None:
            return data
        if data is None:
            return None

        result = data
        try:
            for part in self.get_address_parts(address):
                if result is None:
                    return None
                if self.part_is_digit(part):
                    result = result[int(part)]
                elif self.part_is_function(part):
                    func_name, func_args = self.parse_function(part)
                    result = self.exec_function(func_name, func_args, result)
                else:
                    result = result[part]
            logger.debug('result: %r(%s)', result, result.__class__.__name__)
            return result
        except (KeyError, IndexError), e:
            logger.exception(e)
            return None

    def get_address_parts(self, address):
        parts = address.split('=>')
        parts = [x.strip() for x in parts]
        parts = [x for x in parts if x]
        logger.debug('parts: %s', parts)
        return parts

    def part_is_digit(self, part):
        return part.isdigit()

    def part_is_function(self, part):
        return Schema.function_pattern.match(part) is not None

    def parse_function(self, part):
        match = Schema.function_pattern.match(part)
        fname = match.group(1)
        fargs = {}
        for arg in match.group(2).split(','):
            name, value = arg.split('=')
            fargs[name.strip()] = value.strip()
        return fname, fargs

    def exec_function(self, func_name, func_args, data):
        if func_name == 'filter':
            return self.exec_function_filter(func_args, data)
        elif func_name == 'hash':
            return self.exec_function_hash(func_args, data)
        else:
            raise RuntimeError('unknown function: %s', func_name)

    def exec_function_filter(self, args, data):
        def filter_func(item):
            for name, value in args.items():
                if item.get(name) != value:
                    return False
            return True

        try:
            result = filter(filter_func, data)
            if len(result) == 0:
                return None
            return result[0]
        except (AttributeError, TypeError), e:
            logger.warn('unexpected data: ' + e.message)
            return None

    def exec_function_hash(self, args, data):
        key = args['key']
        value = data.get(key)
        if value is None:
            return None
        value = str(value)
        return binascii.crc32(value) & 0xffffffff

    @staticmethod
    def load_schema(name, schema_dir=None):
        if schema_dir is None:
            schema_dir = Schema.schema_dir
        filename = os.path.join(schema_dir, '%s.yaml' % name)
        if not os.path.exists(filename):
            logger.warn('could not load schema from: %s', filename)
            return None
        logger.info('schema %s from %s', name, filename)
        with open(filename) as h:
            data = yaml.load(h.read())
        return Schema(data)

    @staticmethod
    def get_available_schemas(schema_dir=None):
        if schema_dir is None:
            schema_dir = get_default_schemas_dir()
        for filename in glob.glob('%s/*.yaml' % schema_dir):
            basename = os.path.basename(filename)
            basename, _ = os.path.splitext(basename)
            yield basename
