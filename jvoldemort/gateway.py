import fcntl
import logging
import os
import random
import select
from subprocess import (check_output,
                        Popen, 
                        PIPE,
                        STDOUT)
from threading import (Lock,
                       Thread)
import time

from py4j.java_gateway import (GatewayClient,
                               JavaGateway)

logger = logging.getLogger(__name__)

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

def _log_stdout(proc_name, process, status):
    process_logger = logging.getLogger(__name__ + '.' + proc_name)
    stream = process.stdout
    fcntl.fcntl(stream.fileno(), fcntl.F_SETFL, fcntl.fcntl(stream.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)
    line = ''
    while process.poll() == None:
        if select.select([stream.fileno()], [], [])[0]:
            line += stream.read()
            while '\n' in line:
                output_line, _, line = line.partition('\n')
                if output_line.strip().endswith('Gateway starting'):
                    status[0] = True
                elif output_line:
                    process_logger.info(output_line)
        else:
            time.sleep(1)
    status[0] = False

def _create_gateway(bootstrap_urls):
    gateway_port = 25333 if not _gateways else max(_gateways.itervalues())[0] + 1
    for _ in xrange(5):
        taken_ports = _get_taken_ports()
        while gateway_port in taken_ports:
            gateway_port += 1
        logger.debug("Trying to create Py4J gateway on port %d", gateway_port)
        process = Popen('java -cp %s com.mojn.VoldemortPython %d %s' % (_jar_file, gateway_port, ' '.join( 'tcp://' + u for u in bootstrap_urls )), shell=True, stdout=PIPE, stderr=STDOUT)
        status = [False]
        output_process_thread = Thread(target=_log_stdout, args=('Voldemort-at-' + '/'.join(bootstrap_urls), process, status))
        output_process_thread.daemon = True
        output_process_thread.start()
        logger.debug("Process created")
        for process_running_attempt in xrange(5):
            time.sleep(2**process_running_attempt)
            if status[0]:
                break;
        if status[0]:
            logger.debug("JVM running - trying to connect")
            for connection_attempt in xrange(5):
                time.sleep(2**connection_attempt)
                try:
                    gateway = JavaGateway(GatewayClient(port=gateway_port), auto_convert=False)
                except Exception: # pylint: disable=W0703
                    if connection_attempt == 4:
                        logger.warning('Could not connect to java gateway server at port %d' % (gateway_port,))
                else:
                    return (gateway_port, gateway, output_process_thread)
        else:
            process.terminate()
        gateway_port += random.randint(1,5)
    raise IOError('Could not establish java gateway server after having tried five different ports')

