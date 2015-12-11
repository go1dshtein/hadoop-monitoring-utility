import pytest

from monitoring.utils import get_snmp_name, human_size_format


FIXTURES = [
   ('hadoop', 'hadoop'),
   ('hadoop.hdfs', 'hadoopHdfs'),
   ('hadoop.hdfs.namenode', 'hadoopHdfsNamenode'),
   ('hadoop.yarn.resource-manager', 'hadoopYarnResourceManager'),
]


@pytest.mark.parametrize(
    'name, expected',
    FIXTURES,
    ids=zip(*FIXTURES)[0])
def test_get_snmp_name(name, expected):
    assert get_snmp_name(name) == expected


FIXTURES = [
    (13, '13.0B'),
    (1024, '1.0KiB'),
    (2048, '2.0KiB'),
    (1048576, '1.0MiB'),
    (1073741824, '1.0GiB'),
]


@pytest.mark.parametrize(
    'value, expected',
    FIXTURES,
    ids=zip(*FIXTURES)[1])
def test_human_size_format(value, expected):
    assert human_size_format(value) == expected
