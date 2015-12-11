import pytest
import mock

from collections import namedtuple

import requests
from monitoring.locator import HttpServiceLocator


@pytest.fixture
def locator():
    return HttpServiceLocator()


FIXTURES = [
    ({}, 'http://localhost:80'),
    ({'host': 'hadoop'}, 'http://hadoop:80'),
    ({'port': '8888'}, 'http://localhost:8888'),
    ({'host': 'hadoop', 'port': '8888'}, 'http://hadoop:8888')
]


@pytest.mark.parametrize('kwargs, expected', FIXTURES)
def test_endpoint(kwargs, expected):
    locator = HttpServiceLocator(**kwargs)
    assert locator.url == expected
    assert locator.endpoint() == expected


FIXTURES = [
    (200, True),
    (302, True),
    (400, False),
    (404, False),
    (405, True),
    (None, False),
]


@pytest.mark.parametrize('code, result', FIXTURES)
def test_exists(locator, monkeypatch, code, result):
    if code is None:
        def head(url):
            raise requests.exceptions.ConnectionError('error')
    else:
        def head(url):
            response = namedtuple('Response', ('status_code',))
            return response(status_code=code)

    monkeypatch.setattr(requests, 'head', head)

    assert locator.exists() == result
