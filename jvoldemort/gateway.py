import logging
import os
from subprocess import (check_output,
                        Popen, 
                        PIPE,
                        STDOUT)
from threading import (Lock,
                       Thread)
import time

from py4j.java_gateway import (GatewayClient,
                               JavaGateway)

_gateways = {}
_gateway_lock = Lock()
_jar_file = os.path.join(os.path.dirname(__file__), 'voldemort-python.jar')

def Gateway(bootstrap_urls):
    bootstrap_urls = tuple(sorted(bootstrap_urls))
    result = _gateways.get(bootstrap_urls)
    if result is None:
        with _gateway_lock:
            result = _gateways.get(bootstrap_urls)
            if result is None:
                result = _gateways[bootstrap_urls] = _create_gateway(bootstrap_urls)
    return result[1]

def _get_taken_ports():
    return tuple( int(l.split()[3].split(':')[-1]) for l in check_output('netstat -nptl', shell=True, stderr=STDOUT).splitlines() if 'LISTEN' in l )

def _log_stdout(proc_name, process):
    logger = logging.getLogger(__name__ + '.' + proc_name)
    stream = process.stdout
    while True:
        logger.info(stream.readline())

def _create_gateway(bootstrap_urls):
    gateway_port = 25333 if not _gateways else max(_gateways.itervalues())[0] + 1
    taken_ports = _get_taken_ports()
    while gateway_port in taken_ports:
        gateway_port += 1
    process = Popen('java -cp %s com.mojn.VoldemortPython %d %s' % (_jar_file, gateway_port, ' '.join( 'tcp://' + u for u in bootstrap_urls )), shell=True, stdout=PIPE, stderr=STDOUT)
    output_process_thread = Thread(target=_log_stdout, args=('Voldemort-at-' + '/'.join(bootstrap_urls), process))
    output_process_thread.daemon = True
    output_process_thread.start()
    for attempt in xrange(5):
        time.sleep(2**attempt)
        try:
            gateway = JavaGateway(GatewayClient(port=gateway_port), auto_convert=False)
        except Exception: # pylint: disable=W0703
            if attempt == 4:
                raise IOError('Could not connect to java gateway server at port %d' % (gateway_port,))
        else:
            break
    return (gateway_port, gateway, output_process_thread)
