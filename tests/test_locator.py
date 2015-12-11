import pytest
import mock
import os


from monitoring.locator import ServiceLocator, Locator, DummyLocator


@pytest.fixture
def dummy_locator():
    return DummyLocator()


@pytest.fixture
def service_locator():
    return ServiceLocator()


@pytest.fixture
def locator_config():
    return os.path.join(os.path.dirname(__file__), 'data', 'locator.yaml')


def test_singleton():
    assert id(ServiceLocator()) == id(ServiceLocator())


def test_add(service_locator, dummy_locator):
    service_locator.add('unittest', dummy_locator)
    assert service_locator.locators == {'unittest': dummy_locator}


def test_add_wrong_class(service_locator):
    with pytest.raises(TypeError):
        service_locator.add('unittest', 'some value')


def test_exists(service_locator, dummy_locator):
    service_locator.add('unittest', dummy_locator)
    assert set(service_locator.exists()) == set(['unittest'])


def test_no_exists(service_locator, dummy_locator):
    service_locator.add('unittest', dummy_locator)
    dummy_locator.is_exist = False
    assert set(service_locator.exists()) == set()


def test_endpoint(service_locator, dummy_locator):
    service_locator.add('unittest', dummy_locator)
    assert service_locator.endpoint('unittest') == 'dummy://'


def test_endpoint_no_service(service_locator, dummy_locator):
    with pytest.raises(KeyError):
        service_locator.endpoint('unittest')


def test_read_config(service_locator, locator_config):
    assert service_locator.read_config(locator_config) == {
        'unittest': {'class': 'DummyLocator'},
        'unittest-argument': {'class': 'DummyLocator', 'key': 'value'}
    }


FIXTURES = [
    ({'class': 'DummyLocator'}, {}, (DummyLocator, {})),
    ({'class': 'DummyLocator', 'key': 'value'}, {},
     (DummyLocator, {'key': 'value'})),
    ({'class': 'DummyLocator'}, {'key': 'value'},
     (DummyLocator, {})),
    ({'class': 'DummyLocator', 'key': 'value'},
     {'another key': 'value'},
     (DummyLocator, {'key': 'value'})),
    ({'class': 'DummyLocator', 'key': 'value'},
     {'key': 'another value'},
     (DummyLocator, {'key': 'another value'})),
]


@pytest.mark.parametrize('value, updates, expected', FIXTURES)
def test_get_class_and_args(service_locator, value, updates, expected,
                            monkeypatch):
    monkeypatch.setattr('monitoring.locator.DummyLocator', DummyLocator)
    assert service_locator.get_class_and_args(value, updates) == expected


def test_load_config(service_locator, locator_config):
    service_locator.load_config(locator_config)
    assert service_locator.locators[
        'unittest'].kwargs == {}
    assert service_locator.locators[
        'unittest-argument'].kwargs == {'key': 'value'}
