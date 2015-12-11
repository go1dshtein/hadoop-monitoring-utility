import pytest
import mock
import os


from monitoring.schema import Schema


@pytest.fixture
def schema_dir():
    return os.path.join(os.path.dirname(__file__), 'data', 'schemas')


@pytest.fixture
def schema(schema_dir):
    return Schema.load_schema('test', schema_dir)


@pytest.fixture
def response():
    return {
        'table': [
          {
            'version': "1"
          },
          {
            'version': 'last',
            'runs': [
              {
                'name': 'first',
                'count': 1
              },
              {
                'name': 'second',
                'count': 3
              }
            ]
          }
        ],
        'memory': [100, 200]
      }


def test_get_available_schemas(schema_dir):
    assert set(Schema.get_available_schemas(schema_dir)) == set(['test'])


def test_get_available_schemas_default():
    assert set(Schema.get_available_schemas()) == set([
        'hdfs.datanode',
        'hdfs.journalnode',
        'hdfs.namenode',
        'hdfs.secondarynamenode',
        'hdfs.zkfc.jmx',
        'hive.metastore.jmx',
        'hive.server2.jmx',
        'impala.catalog',
        'impala.server',
        'impala.statestore',
        'oozie',
        'oozie.jmx',
        'yarn.history-server.jmx',
        'yarn.node-manager.jmx',
        'yarn.resource-manager',
        'yarn.resource-manager.jmx',
        'zookeeper.jmx',
        ])


def test_load_schema_not_found(schema_dir):
    assert Schema.load_schema('unknown', schema_dir) is None


def test_load_schema(schema_dir):
    assert isinstance(Schema.load_schema('test', schema_dir), Schema)


def test_scan_without_request(schema):
    assert schema.scan('1', 'unit') == {
        'unit.test.memory.available': {
            'description': None,
            'name': 'unit.test.memory.available',
            'oid': '1.1.2.2',
            'snmp': 'unitTestMemoryAvailable',
            'type': 'Counter64',
            'unit': 'bytes',
            'value': None,
        },
        'unit.test.memory.used': {
            'description': None,
            'name': 'unit.test.memory.used',
            'oid': '1.1.2.1',
            'snmp': 'unitTestMemoryUsed',
            'type': 'Counter64',
            'unit': 'bytes',
            'value': None,
        },
        'unit.test.table-metric.count': {
            'description': 'show how many times this task was run',
            'name': 'unit.test.table-metric.count',
            'oid': '1.1.1.3',
            'snmp': 'unitTestTableMetricCount',
            'type': 'Counter32',
            'unit': 'times',
            'value': None,
        },
        'unit.test.table-metric.name': {
            'description': None,
            'name': 'unit.test.table-metric.name',
            'oid': '1.1.1.2',
            'snmp': 'unitTestTableMetricName',
            'type': 'OCTET STRING',
            'unit':  '',
            'value': None,
        },
        'unit.test.table-metric.index': {
            'description': None,
            'name': 'unit.test.table-metric.index',
            'oid': '1.1.1.1',
            'snmp': 'unitTestTableMetricIndex',
            'type': 'INTEGER',
            'unit':  '',
            'value': None,
        },
    }


def test_scan(schema, response):
    def executor(x, y):
        return response
    schema.set_request_executor(executor)

    assert schema.scan('1', 'unit') == {
        'unit.test.memory.available': {
            'description': None,
            'name': 'unit.test.memory.available',
            'oid': '1.1.2.2',
            'snmp': 'unitTestMemoryAvailable',
            'type': 'Counter64',
            'unit': 'bytes',
            'value': 200,
        },
        'unit.test.memory.used': {
            'description': None,
            'name': 'unit.test.memory.used',
            'oid': '1.1.2.1',
            'snmp': 'unitTestMemoryUsed',
            'type': 'Counter64',
            'unit': 'bytes',
            'value': 100,
        },
        'unit.test.table-metric.count.2456940119': {
            'description': 'show how many times this task was run',
            'name': 'unit.test.table-metric.count.2456940119',
            'oid': '1.1.1.3.2456940119',
            'snmp': 'unitTestTableMetricCount.2456940119',
            'type': 'Counter32',
            'unit': 'times',
            'value': 1,
        },
        'unit.test.table-metric.name.2456940119': {
            'description': None,
            'name': 'unit.test.table-metric.name.2456940119',
            'oid': '1.1.1.2.2456940119',
            'snmp': 'unitTestTableMetricName.2456940119',
            'type': 'OCTET STRING',
            'unit':  '',
            'value': 'first',
        },
        'unit.test.table-metric.index.2456940119': {
            'description': None,
            'name': 'unit.test.table-metric.index.2456940119',
            'oid': '1.1.1.1.2456940119',
            'snmp': 'unitTestTableMetricIndex.2456940119',
            'type': 'INTEGER',
            'unit':  '',
            'value': 2456940119,
        },
        'unit.test.table-metric.count.3055489385': {
            'description': 'show how many times this task was run',
            'name': 'unit.test.table-metric.count.3055489385',
            'oid': '1.1.1.3.3055489385',
            'snmp': 'unitTestTableMetricCount.3055489385',
            'type': 'Counter32',
            'unit': 'times',
            'value': 3,
        },
        'unit.test.table-metric.name.3055489385': {
            'description': None,
            'name': 'unit.test.table-metric.name.3055489385',
            'oid': '1.1.1.2.3055489385',
            'snmp': 'unitTestTableMetricName.3055489385',
            'type': 'OCTET STRING',
            'unit':  '',
            'value': 'second',
        },
        'unit.test.table-metric.index.3055489385': {
            'description': None,
            'name': 'unit.test.table-metric.index.3055489385',
            'oid': '1.1.1.1.3055489385',
            'snmp': 'unitTestTableMetricIndex.3055489385',
            'type': 'INTEGER',
            'unit':  '',
            'value': 3055489385,
        },
    }


def test_exec_function_hash(schema):
    args = {'key': 'name'}
    data = {'name': 'first'}
    assert schema.exec_function_hash(args, data) == 2456940119


def test_exec_function_hash_no_key(schema):
    args = {'nokey': 'name'}
    data = {'name': 'first'}
    with pytest.raises(KeyError):
        schema.exec_function_hash(args, data)


def test_exec_function_hash_no_key_value(schema):
    args = {'key': 'name'}
    data = {'noname': 'first'}
    assert schema.exec_function_hash(args, data) is None


FIXTURES = [
  ({'name': 'first'},
   {'name': 'first', 'version': '1', 'count': 1}),
  ({'name': 'first', 'version': 'last'},
   {'name': 'first', 'version': 'last', 'count': 2}),
  ({'name': 'third'}, None),
]


@pytest.mark.parametrize(
    'args, expected', FIXTURES,
    ids=['one key', 'two keys', 'not found'])
def test_exec_function_filter(schema, args, expected):
    data = [{'name': 'first', 'version': '1', 'count': 1},
            {'name': 'first', 'version': 'last', 'count': 2},
            {'name': 'second', 'version': 'last', 'count': 3}]
    assert schema.exec_function_filter(args, data) == expected


FIXTURES = [
  'string',
  10,
  {'key': 'value'},
  ['string', 10]
]


@pytest.mark.parametrize('data', FIXTURES)
def test_exec_function_not_valid_list(schema, data):
    args = {'name': 'first'}
    assert schema.exec_function_filter(args, data) is None


FIXTURES = [
  ('filter', 'exec_function_filter'),
  ('hash', 'exec_function_hash'),
  ('unknown', None)
]


@pytest.mark.parametrize('name, func', FIXTURES, ids=zip(*FIXTURES)[0])
def test_exec_function(schema, name, func):
    if func is None:
        with pytest.raises(RuntimeError):
            schema.exec_function(name, {}, {})
    else:
        func_mock = mock.Mock()
        setattr(schema, func, func_mock)
        schema.exec_function(name, {}, {})
        assert func_mock.mock_calls == [mock.call({}, {})]


FIXTURES = [
    ('func(first=1,second=name)', 'func',
     {'first': '1', 'second': 'name'}),
    ('func_name( first = 1, second = name )', 'func_name',
     {'first': '1', 'second': 'name'}),
]


@pytest.mark.parametrize(
    'part, name, args', FIXTURES, ids=range(len(FIXTURES)))
def test_parse_function(schema, part, name, args):
    assert schema.parse_function(part) == (name, args)


FIXTURES = [
    (' => value => 3 => => => 1', ['value', '3', '1']),
    (' => value => func(a = 4) => 1', ['value', 'func(a = 4)', '1']),
    ('', []),
    (' => ', []),
]


@pytest.mark.parametrize('address, parts', FIXTURES, ids=range(len(FIXTURES)))
def test_get_address_parts(schema, address, parts):
    assert schema.get_address_parts(address) == parts


FIXTURES = [
    ('table => filter(version=1) => runs', None),
    ('unknown', None),
    ('table => filter(version=last) => '
     'runs => filter(name=first) => count', 1),
    ('memory => 0', 100),
    ('memory => 1', 200),
    ('memory => 2', None),
    ('table => 1 => runs => 0 => hash(key=name)', 2456940119),
    ('table => 1 => runs => 0 => name', 'first'),
    ('table => 0 => runs', None)
]


@pytest.mark.parametrize(
    'address, expected', FIXTURES, ids=range(len(FIXTURES)))
def test_get_value(schema, response, address, expected):
    assert schema.get_value(response, address) == expected


def test_get_value_no_data(schema):
    assert schema.get_value(None, 'address') is None


def test_get_value_no_address(schema, response):
    assert schema.get_value(response, None) == response
