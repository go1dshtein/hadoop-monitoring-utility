import pytest
import mock
import subprocess


from monitoring.collector import Client, JMXClient


@pytest.fixture
def client():
    endpoint = 'process://unittest@1111'
    result = JMXClient(endpoint)
    assert isinstance(result, Client)
    return result


def test_init(client):
    assert client.user == 'unittest'
    assert client.pid == 1111


FIXTURES = [
    ({'bean': 'java.lang:Bean', 'attr': 'BeanAttr'},
     'get -b java.lang:Bean -s -q BeanAttr\n'),
    ('java.lang:Bean;BeanAttr', None),
    (['java.lang:Bean;BeanAttr'], None),
    ({'value': 'java.lang:Bean;BeanAttr'}, None)
]


@pytest.mark.parametrize('query, expected', FIXTURES)
def test_create_input(client, query, expected):
    if expected is None:
        with pytest.raises(KeyError):
            client.create_input(query)
    else:
        assert client.create_input(query) == expected


def test_get_command(client):
    assert client.get_command() == 'sudo -u unittest /usr/bin/jmxterm -l 1111'


def test_parse_output(client):
    data = """
{
  "committed" = 29556736;
  "init" = 30504832;
  "max" = 259522560;
  "used" = 15615120;
 }
    """

    assert client.parse_output(data) == {
        'committed': 29556736,
        'init': 30504832,
        'max': 259522560,
        'used': 15615120
    }


def test_run_command(client, monkeypatch):
    proc = mock.Mock()
    proc.returncode = 0
    proc.communicate.return_value = ['output', 'error']
    data = 'data'

    def popen(command, **kwargs):
        assert command == client.get_command()
        return proc

    monkeypatch.setattr(subprocess, 'Popen', popen)

    assert client.run_command(client.get_command(), data) == 'output'
    assert proc.stdin.write.mock_calls == [mock.call(data)]


def test_run_command_fail(client, monkeypatch):
    proc = mock.Mock()
    proc.returncode = 1
    proc.communicate.return_value = ['output', 'error']
    data = 'data'

    def popen(command, **kwargs):
        assert command == client.get_command()
        return proc

    monkeypatch.setattr(subprocess, 'Popen', popen)

    assert client.run_command(client.get_command(), data) is None
    assert proc.stdin.write.mock_calls == [mock.call(data)]


def test_make_request(client, monkeypatch):
    data = """
{
  "committed" = 29556736;
  "init" = 30504832;
  "max" = 259522560;
  "used" = 15615120;
 }
    """
    proc = mock.Mock()
    proc.returncode = 0
    proc.communicate.return_value = [data, '']
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: proc)

    assert client.make_request(
        {'bean': 'java.lang:type=Memory', 'attr': 'HeapMemoryUsage'}) == {
        'committed': 29556736,
        'init': 30504832,
        'max': 259522560,
        'used': 15615120
    }


def test_make_request_failed(client, monkeypatch):
    proc = mock.Mock()
    proc.returncode = 1
    proc.communicate.return_value = ['', 'ERROR']
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: proc)

    assert client.make_request(
        {'bean': 'java.lang:type=Memory', 'attr': 'HeapMemoryUsage'}) is None
