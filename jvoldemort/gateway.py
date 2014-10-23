import fcntl
import logging
import os
import random
import select
from subprocess import (check_output,
                        Popen, 
                        PIPE,
                        STDOUT)
from threading import (RLock,
                       Thread)
import time

from py4j.java_gateway import (GatewayClient,
                               JavaGateway)
from py4j.protocol import (ERROR,
                           Py4JNetworkError)

logger = logging.getLogger(__package__)

logging.getLogger('py4j.java_gateway').setLevel(logging.WARNING)

_jar_file = os.path.join(os.path.dirname(__file__), 'voldemort-python.jar')

class _RetryOnceGatewayClient(GatewayClient):
    def send_command(self, command, retry=True):
        connection = self._get_connection()
        try:
            response = connection.send_command(command)
            self._give_back_connection(connection)
        except Py4JNetworkError as ex:
            if retry:
                response = self.send_command(command, False)
            else:
                logger.info('Error sending command to gateway: %s', getattr(ex, 'message', '') or str(ex))
                response = ERROR
        return response

class Gateway(object):
    
    _gateways = {}
    _gateway_lock = RLock()

    def __new__(cls, bootstrap_urls):
        bootstrap_urls = tuple(sorted(bootstrap_urls))
        result = cls._gateways.get(bootstrap_urls)
        if result is None:
            with cls._gateway_lock:
                result = cls._gateways.get(bootstrap_urls)
                if result is None:
                    result = cls._gateways[bootstrap_urls] = object.__new__(cls, bootstrap_urls)
        return result

    def __init__(self, bootstrap_urls):
        with self._gateway_lock:
            from . import JAVA_OPTS
            self.bootstrap_urls = bootstrap_urls
            gateway_port = 25333 if len(self._gateways) == 1 else max( g.gateway_port for g in self._gateways.itervalues() if g is not self ) + 1
            self.gateway = gateway = None
            for _ in xrange(5):
                taken_ports = self._get_taken_ports()
                while gateway_port in taken_ports:
                    gateway_port += 1
                logger.debug("Trying to create Py4J gateway on port %d", gateway_port)
                process = Popen('java -cp %s %s com.mojn.VoldemortPython %d %s' % (_jar_file, JAVA_OPTS, gateway_port, ' '.join( 'tcp://' + u for u in bootstrap_urls )), shell=True, stdout=PIPE, stderr=STDOUT)
                status = [False]
                output_process_thread = Thread(target=self._log_stdout, args=('Voldemort-at-' + '/'.join(bootstrap_urls), process, status))
                output_process_thread.daemon = True
                output_process_thread.start()
                logger.debug("Process created")
                for process_running_attempt in xrange(5):
                    time.sleep(2**process_running_attempt)
                    if status[0]:
                        break
                if status[0]:
                    logger.debug("JVM running - trying to connect")
                    for connection_attempt in xrange(5):
                        try:
                            gateway = JavaGateway(_RetryOnceGatewayClient(port=gateway_port), auto_convert=False)
                            for alive_attempt in xrange(5):
                                try:
                                    if gateway.isAlive():
                                        break
                                except Exception: # pylint: disable=W0703
                                    pass
                                if alive_attempt == 4:
                                    raise Exception()
                                else:
                                    time.sleep(2**alive_attempt)
                        except Exception: # pylint: disable=W0703
                            gateway = None
                            if connection_attempt == 4:
                                logger.warning('Could not connect to java gateway server at port %d', gateway_port)
                        if gateway is not None:
                            self.gateway_port = gateway_port
                            self.process = process
                            self.gateway = gateway
                            self.output_process_thread = output_process_thread
                            break
                        else:
                            time.sleep(2**connection_attempt)
                else:
                    process.terminate()
                if self.gateway is not None:
                    break
                gateway_port += random.randint(1,5)
        if self.gateway is None:
            raise IOError('Could not establish java gateway server after having tried five different ports')
            
    def __getattr__(self, attribute_name):
        if attribute_name in ('gateway_port', 'process', 'gateway', 'output_process_thread', 'bootstrap_urls'):
            raise AttributeError('Gateway does not have an attribute called ' +  attribute_name)
        if getattr(self, 'gateway', '') == 'closed':
            raise AttributeError('Closed Gateway does not have an attribute called ' +  attribute_name)
        return getattr(self.gateway, attribute_name)

    def close(self):
        with self._gateway_lock:
            logger.debug("Sealing Java gateway to " + str(self.bootstrap_urls))
            if self._gateways.get(self.bootstrap_urls) is self:
                del self._gateways[self.bootstrap_urls]
            logger.debug("Closing Java gateway to " + str(self.bootstrap_urls))
            try:
                self.gateway.shutdown()
            except (AttributeError, TypeError):
                pass
            self.gateway = 'closed'
            self.process.terminate()

    @classmethod
    def _get_taken_ports(cls):
        return tuple( int(l.split()[3].split(':')[-1]) for l in check_output('netstat -nptl', shell=True, stderr=STDOUT).splitlines() if 'LISTEN' in l )
    
    @classmethod
    def _log_stdout(cls, proc_name, process, status):
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
