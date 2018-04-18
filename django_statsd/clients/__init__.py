import socket
import time

try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

from django.conf import settings

_statsd = None


def get(name, default):
    try:
        return getattr(settings, name, default)
    except ImportError:
        return default


def get_client():
    from common.logger import logger
    client = get('STATSD_CLIENT', 'statsd.client')
    host = get('STATSD_HOST', 'localhost')
# This is causing problems with statsd
# gaierror ([Errno -9] Address family for hostname not supported)
# TODO: figure out what to do here.
    tries = 10
    for i in range(tries):
        try:
            host = socket.gethostbyaddr(host)[2][0]
            logger.info('Resolved statsd host to {}'.format(host))
        except socket.gaierror:
            if i == tries - 1:
                raise
            else:
                logger.exception('Failed to resolve statsd host {}, try {}/{}'.format(host, i+1, tries))
                time.sleep(5)
    port = get('STATSD_PORT', 8125)
    prefix = get('STATSD_PREFIX', None)
    return import_module(client).StatsClient(host=host, port=port, prefix=prefix)

if not _statsd:
    _statsd = get_client()

statsd = _statsd
