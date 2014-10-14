import logging
import os
from subprocess import (check_call,
                        check_output,
                        Popen, 
                        PIPE)
from threading import (Lock,
                       Thread)
import time

from py4j.java_gateway import (GatewayClient,
                               JavaGateway)

_gateways = {}
_gateway_lock = Lock()

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
    return tuple( int(l.split()[3].split(':')[-1]) for l in check_output('netstat -nptl', shell=True).splitlines() if 'LISTEN' in l )

def _log_stdout(proc_name, process):
    logger = logging.getLogger(__name__ + '.' + proc_name)
    stream = process.stdout
    while True:
        logger.info(stream.readline())

def _get_jar_path():
    lib_path = 'build/libs'
    if os.path.isdir(lib_path):
        for f in os.listdir(lib_path):
            if f.startswith('voldemort-python') and f.endswith('-all.jar'):
                return os.path.join(lib_path, f)
    check_call('gradle shadowJar', shell=True)
    for f in os.listdir(lib_path):
        if f.startswith('voldemort-python') and f.endswith('-all.jar'):
            return os.path.join(lib_path, f)
    raise IOError('Could not find nor create voldemort-python jar')

def _create_gateway(bootstrap_urls):
    gateway_port = 25333 if not _gateways else max(_gateways.itervalues())[0] + 1
    taken_ports = _get_taken_ports()
    while gateway_port in taken_ports:
        gateway_port += 1
    process = Popen('java -cp %s com.mojn.VoldemortPython %d %s' % (_get_jar_path(), gateway_port, ' '.join( 'tcp://' + u for u in bootstrap_urls )), shell=True, stdout=PIPE, stdin=PIPE)
    output_process_thread = Thread(target=_log_stdout, args=('Voldemort-at-' + '/'.join(bootstrap_urls), process))
    output_process_thread.daemon = True
    output_process_thread.start()
    print "Started"
    for attempt in xrange(5):
        time.sleep(2**attempt)
        try:
            gateway = JavaGateway(GatewayClient(port=gateway_port), auto_convert=False)
        except Exception: # pylint: disable=W0703
            if attempt == 4:
                raise
        else:
            break
    return (gateway_port, gateway, output_process_thread)
