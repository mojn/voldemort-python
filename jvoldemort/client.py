import logging

from .gateway import Gateway
from py4j.protocol import Py4JError

logger = logging.getLogger(__package__)

class VoldemortException(Exception):
    pass

class _IdentityRead(object):
    def reads(self, value):
        return value
    def writes(self, value):
        return value

_default_reader = _IdentityRead()

class StoreClient:
    
    def __init__(self, store_name, bootstrap_urls):
        self.store_name = store_name
        try:
            self._java_gateway = Gateway(tuple( '%s:%d' % (h,p) for (h,p) in bootstrap_urls ))
        except (IOError, Py4JError) as ex:
            raise VoldemortException(ex.message)
        self.key_serializer = self.value_serializer = _default_reader

    def _get_value(self, result):
        if isinstance(result, bytearray):
            result = str(result)
        return self.value_serializer.reads(result)
        
    def get(self, key):
        """Execute a get request. Returns a list of (value, version) pairs."""
        try:
            unwrapped_result = result = self._java_gateway.get(self.store_name, self.key_serializer.writes(key))
            if result is not None:
                try:
                    unwrapped_result = [[self._get_value(result[0]), result[1]]]
                finally:
                    self._java_gateway.detach(result)
            return unwrapped_result
        except Py4JError as ex:
            raise VoldemortException("Error getting result from py4j bridge: " + getattr(ex, 'message', '') or str(ex))

    def get_all(self, keys):
        raise NotImplementedError('Not implemented yet')

    def put(self, key, value, version = None):
        raise NotImplementedError('Not implemented yet')

    def maybe_put(self, key, value, version = None):
        raise NotImplementedError('Not implemented yet')

    def delete(self, key, version = None):
        raise NotImplementedError('Not implemented yet')

    def close(self):
        self._java_gateway.close()
    
