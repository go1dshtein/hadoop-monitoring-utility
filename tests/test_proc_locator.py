import pytest
import mock

import psutil

from collections import namedtuple

from monitoring.locator import ProcessLocator


@pytest.fixture
def processes():
    process = namedtuple('Process', ('cmdline', 'pid', 'username'))
    processes = [
        process(['java', '-jar', 'unittest.jar'], 10, 'unittest'),
        process(['python', '-m', 'module', 'arg', 'two'], 20, 'unittest'),
    ]
    return processes


@pytest.fixture
def locator():
    return ProcessLocator()


def test_get_processes(locator, processes, monkeypatch):
    monkeypatch.setattr(psutil, 'process_iter', lambda: processes)

    assert locator.get_processes() == [
        ('java -jar unittest.jar', 10, 'unittest'),
        ('python -m module arg two', 20, 'unittest')
    ]


def test_exists(locator, processes, monkeypatch):
    monkeypatch.setattr(psutil, 'process_iter', lambda: processes)
    pattern = '.*unittest.jar$'
    locator.pattern = pattern

    assert locator.exists() is True
    assert locator.pid == 10
    assert locator.user == 'unittest'


def test_not_exists(locator, processes, monkeypatch):
    monkeypatch.setattr(psutil, 'process_iter', lambda: processes)
    pattern = '.*hadoop.jar$'
    locator.pattern = pattern

    assert locator.exists() is False
    assert locator.pid is None
    assert locator.user is None


def test_endpoint(locator):
    locator.pid = 10
    locator.user = 'unittest'

    assert locator.endpoint() == 'process://unittest@10'
