
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    from .client import StoreClient, VoldemortException
    import argparse
    parser = argparse.ArgumentParser('Voldemort client test interface')
    parser.add_argument('-s', '--store', type=str, default='signal', help='Store to access')
    parser.add_argument('-hs', '--hosts', type=str, nargs='+', help='Hosts for voldemort bootstrap')
    parser.add_argument('command', type=str, help='Hosts for voldemort bootstrap')
    args = parser.parse_args()

    import base64
    class _Base64ValueSerializer(object):
        def reads(self, bytestring):
            return base64.b64encode(bytestring)

    connection = StoreClient(args.store, [ (h.split(':')[0], int(h.split(':')[1])) for h in args.hosts ] )
    connection.value_serializer = _Base64ValueSerializer()
    print eval(args.command.replace('{}', 'connection'))
    import time
    time.sleep(2)