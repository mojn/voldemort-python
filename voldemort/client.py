from .gateway import Gateway

class StoreClient:
    
    def __init__(self, store_name, bootstrap_urls):
        self.store_name = store_name
        self._java_client = Gateway(tuple( '%s:%d' % (h,p) for (h,p) in bootstrap_urls )).getClient(store_name)
        
    def get(self, key):
        """Execute a get request. Returns a list of (value, version) pairs."""
        result = self._java_client.get(key)
        return result and (result.getValue(), result.getVersion())        

    def get_all(self, keys):
        return self._java_client.get_all(keys)

    def put(self, key, value, version = None):
        return self._java_client.put(key, value, version)

    def maybe_put(self, key, value, version = None):
        try:
            return self.put(key, value, version)
        except Exception: # pylint: disable=W0703
            return None

    def delete(self, key, version = None):
        return self._java_client.delete(key, version)

    def close(self):
        return self._java_client.close()




