import logging
import os
import sys


def setup_logging(config):
    try:
        from logging.config import dictConfig
    except ImportError:
        # python2.6's logging.config module has no dictConfig function
        # let's use backported version
        from dictconfig import dictConfig

    if os.path.exists('/dev/log'):
        logsocket = '/dev/log'
    else:
        logsocket = '/var/run/syslog'

    logconfig = {
        'version': 1,
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'file',
                'filename': config.filename,
                'backupCount': 5,
                'maxBytes': 1048576,
            },
            'syslog': {
                'class': 'logging.handlers.SysLogHandler',
                'formatter': 'syslog',
                'facility': 'daemon',
                'address': logsocket,
                'level': 'WARNING',
            },
        },
        'formatters': {
            'file': {
                'format': '%(asctime)s: %(levelname)s: %(name)s: %(message)s',
            },
            'syslog': {
                'format': 'hadoop-monitoring: %(name)s: %(message)s',
            },
        },
        'root': {
            'handlers': ['file', 'syslog'],
            'level': config.level,
        },
        'loggers': {
            'monitoring': {},
            'urllib3': {
                'level': 'ERROR',
            },
            'requests': {
                'level': 'ERROR',
            },
        }
    }
    if config.filename is None:
        logconfig['handlers']['file'] = {
            'class': 'logging.StreamHandler',
            'formatter': 'file',
            'stream': sys.stderr
        }
    dictConfig(logconfig)


def human_size_format(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return '%3.1f%s%s' % (num, unit, suffix)
        num /= 1024.0
    return '%.1f%s%s' % (num, 'Yi', suffix)


def get_snmp_name(name):
    name = name.split('.')
    name = [x.title() for x in name]
    prefix = name[0].lower()
    suffix = name[-1]
    if len(name) > 1 and (suffix.isdigit() or suffix.startswith('-')):
        name[-1] = '.%s' % suffix
    name = prefix + ''.join(name[1:])
    return name.replace('-', '')
