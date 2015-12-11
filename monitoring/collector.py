import json
import logging
import os
import re
import subprocess

logger = logging.getLogger(__name__)


class Client(object):
    def __init__(self, endpoint):
        raise NotImplementedError('init requeires one argument - endpoint')

    def make_request(self, query):
        raise NotImplementedError('abstract method is called')


class HTTPClient(Client):
    def __init__(self, endpoint):
        self.endpoint = endpoint.rstrip('/')

    def make_request(self, query):
        import requests

        url = '%s%s' % (self.endpoint, query)
        headers = {'accept': 'application/json'}
        logger.debug('request to %s', url)
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return json.loads(response.text)
        except Exception:
            logger.exception('could not retrieve data')
            return None


class JMXClient(Client):
    def __init__(self, endpoint):
        self.user = endpoint.split('@')[0].split('://')[-1]
        self.pid = int(endpoint.split('@')[-1])

    def make_request(self, query):
        input_data = self.create_input(query)
        logger.debug('request to %s@%d:\n%s', self.user, self.pid, input_data)
        command = self.get_command()
        output = self.run_command(command, input_data)
        if output is None:
            return None
        return self.parse_output(output)

    def parse_output(self, output):
        pattern = re.compile(r'"(.*?)"\s*=\s*(.*?);', re.S | re.U)
        data = pattern.findall(output)
        data = [(key, int(value)) for key, value in data if value.isdigit()]
        return dict(data)

    def run_command(self, command, data):
        proc = subprocess.Popen(
            command, shell=True,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE)
        proc.stdin.write(data)
        out, err = proc.communicate()
        if proc.returncode != 0:
            logger.error('command: %s', command)
            logger.error('return code: %d', proc.returncode)
            logger.error('stdout: \n%s', out)
            logger.error('stderr: \n%s', err)
            return None
        return out

    def get_command(self):
        executable = '/usr/bin/jmxterm'
        return 'sudo -u %s %s -l %s' % (self.user, executable, self.pid)

    def create_input(self, query):
        try:
            bean = query['bean']
            attr = query['attr']
            return 'get -b %s -s -q %s\n' % (bean, attr)
        except Exception, e:
            raise KeyError('invalid query: %s', e.message)


class Collector(object):
    clients = {
        'http': HTTPClient,
        'process': JMXClient,
    }

    def __init__(self, endpoint, schema):
        self.endpoint = endpoint
        self.schema = schema
        self.schema.set_request_executor(self.make_request)

    def make_request(self, query, endpoint=None):
        endpoint = endpoint or self.endpoint
        uri_schema = self.get_uri_schema(endpoint)
        client = Collector.clients[uri_schema](endpoint)
        return client.make_request(query)

    def get_uri_schema(self, endpoint):
        return endpoint.split('://')[0]

    def collect(self, oid, name):
        return self.schema.scan(oid, name)
