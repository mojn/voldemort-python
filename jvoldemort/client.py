from .gateway import Gateway

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
            self._java_client = Gateway(tuple( '%s:%d' % (h,p) for (h,p) in bootstrap_urls )).getClient(store_name)
        except IOError as ex:
            raise VoldemortException(ex.message)
        self.key_serializer = self.value_serializer = _default_reader

    def _get_value(self, result):
        result = result.getValue()
        if isinstance(result, bytearray):
            result = str(result)
        return self.value_serializer.reads(result)
        
    def get(self, key):
        """Execute a get request. Returns a list of (value, version) pairs."""
        result = self._java_client.get(self.key_serializer.writes(key))
        return result and [(self._get_value(result), result.getVersion())]

    def get_all(self, keys):
        raise NotImplementedError('Not implemented yet')

    def put(self, key, value, version = None):
        raise NotImplementedError('Not implemented yet')

    def maybe_put(self, key, value, version = None):
        raise NotImplementedError('Not implemented yet')

    def delete(self, key, version = None):
        raise NotImplementedError('Not implemented yet')

    def close(self):
        return self._java_client.close()




