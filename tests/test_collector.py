import pytest
import mock
import os

import requests

from monitoring.collector import Client, HTTPClient, Collector


@pytest.fixture
def client():
    endpoint = 'http://localhost:50070'
    result = HTTPClient(endpoint)
    assert isinstance(result, Client)
    return result


@pytest.fixture
def schema():
    return mock.Mock()


@pytest.fixture
def http_collector(schema):
    endpoint = 'http://localhost:50070'
    collector = Collector(endpoint, schema)
    return collector


@pytest.fixture
def jmx_collector(schema):
    endpoint = 'process://unittest@1111'
    collector = Collector(endpoint, schema)
    return collector


@pytest.fixture
def collector(http_collector, jmx_collector, request):
    if request.param == 'http':
        return http_collector
    if request.param == 'jmx':
        return jmx_collector


def test_http_make_request(client, monkeypatch):
    response = mock.Mock()
    response.text = '{"key": "value"}'
    monkeypatch.setattr(requests, 'get', lambda *a, **k: response)
    assert client.make_request('/url') == {'key': 'value'}


def test_http_make_request_error(client, monkeypatch):
    response = mock.Mock()
    response.text = '{"key": "value"}'

    def status():
        raise requests.exceptions.HTTPError(400)

    response.raise_for_status.side_effect = status
    monkeypatch.setattr(requests, 'get', lambda *a, **k: response)
    assert client.make_request('/url') is None


def test_http_make_request_no_json(client, monkeypatch):
    response = mock.Mock()
    response.text = '<xml><data/></xml>'
    monkeypatch.setattr(requests, 'get', lambda *a, **k: response)
    assert client.make_request('/url') is None


@pytest.mark.parametrize('collector', ['jmx', 'http'], indirect=True)
def test_collect(collector, schema):
    oid = 'oid'
    name = 'name'
    collector.collect(oid, name)
    assert schema.scan.mock_calls == [mock.call(oid, name)]


@pytest.mark.parametrize(
    'endpoint, expected', [('http://localhost:8080', 'http'),
                           ('process://root@12212', 'process')])
@pytest.mark.parametrize('collector', ['jmx', 'http'], indirect=True)
def test_get_uri_schema(collector, endpoint, expected):
    assert collector.get_uri_schema(endpoint) == expected
