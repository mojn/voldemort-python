import ctypes
import fcntl
import logging
import os
import select
from subprocess import (Popen, 
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

_libc=None
for libc_location in ('/lib/x86_64-linux-gnu/libc.so.6', '/lib/i386-linux-gnu/libc.so.6'):
    try:
        _libc = ctypes.CDLL(libc_location)
    except OSError:
        pass
if _libc is not None:
    logger.info("Cannot find libc.so.6 in any of the standard locations. Guaranteed teardown of child processes not possible.")
    _preexec = lambda : None
else:
    _preexec = lambda : _libc.prctl(1,15)


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

    __slots__ = ('gateway_port', 'process', 'gateway', 'client', 'is_running', 'is_connected', 'output_process_thread', 'bootstrap_urls')

    def _cleanup(self):
        if self.process is not None:
            logger.debug("Closing gateway connection to %d", getattr(self, 'gateway_port', '?'))
        if self.client is not None:
            try:
                self.client.close()
            except Exception as ex:
                logger.debug("Error while closing gateway client: %s", getattr(ex, 'message', '') or str(ex))
        if self.gateway is not None:
            self.gateway.shutdown()
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait()
            except OSError:
                pass # process already gone
        self.is_connected = self.is_running = False
        self.gateway_port = self.client = self.process = self.gateway = None

    def _establish_connection(self, bootstrap_urls):
        from . import JAVA_OPTS
        self.bootstrap_urls = bootstrap_urls
        self.gateway_port = self.client = self.process = self.gateway = None
        for _ in xrange(3):
            self._cleanup()
            logger.debug("Trying to create Py4J gateway")
            self.process = Popen(['java', '-cp', _jar_file] + JAVA_OPTS.split() + ['com.mojn.VoldemortPython'] + [ 'tcp://' + u for u in bootstrap_urls ], 
                                 bufsize=1, preexec_fn=_preexec,
                                 stdout=PIPE, stderr=STDOUT)
            self.is_running = False
            self.output_process_thread = Thread(target=self._log_stdout, args=('Voldemort-at-' + '/'.join(bootstrap_urls), self.process))
            self.output_process_thread.daemon = True
            self.output_process_thread.start()
            logger.debug("Process created")
            for attempt in xrange(5):
                if self.is_running:
                    break
                elif attempt < 4:
                    time.sleep(2**attempt)
            if not self.is_running:
                logger.debug("JVM never started running")
                continue
            for attempt in xrange(5):
                if self.gateway_port:
                    break
                elif attempt < 4:
                    time.sleep(2**attempt)
            if not self.gateway_port:
                logger.debug("JVM never emitted a port number on stdout")
                continue
            logger.debug("Gateway up - trying to connect")
            for attempt in xrange(5):
                try:
                    self.client = _RetryOnceGatewayClient(port=self.gateway_port)
                    self.gateway = JavaGateway(self.client, auto_convert=False)
                    break
                except Exception: # pylint: disable=W0703
                    if attempt < 4:
                        time.sleep(2**attempt)
            if self.gateway is None:
                logger.debug('Could not connect to java gateway server at port %d', self.gateway_port)
                continue
            logger.debug("Connected to JVM - testing gateway initialization")
            for attempt in xrange(5):
                try:
                    if self.gateway.isAlive():
                        self.is_connected = True
                        break
                except Exception: # pylint: disable=W0703
                    if attempt < 4:
                        time.sleep(2**attempt)
            if self.is_connected:
                break
        if not self.is_connected:
            self._cleanup()
            raise IOError('Could not establish java gateway server after trying three times')

    def __init__(self, bootstrap_urls):
        with self._gateway_lock:
            if not getattr(self, 'is_connected', False):
                self._establish_connection(bootstrap_urls)
            
    def __getattr__(self, attribute_name):
        if attribute_name in self.__slots__:
            raise AttributeError('Gateway does not have an attribute called ' +  attribute_name)
        if not getattr(self, 'is_connected', False):
            raise AttributeError('Closed Gateway does not have an attribute called ' +  attribute_name)
        return getattr(self.gateway, attribute_name)

    def close(self):
        with self._gateway_lock:
            logger.debug("Sealing Java gateway to " + str(self.bootstrap_urls))
            if self._gateways.get(self.bootstrap_urls) is self:
                del self._gateways[self.bootstrap_urls]
            logger.debug("Closing Java gateway to " + str(self.bootstrap_urls))
            self._cleanup()

    def __del__(self):
        try:
            logger.debug("Deleting Gateway object " + str(self.bootstrap_urls))
            self._cleanup()
        except Exception:
            pass

    def _log_stdout(self, proc_name, process):
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
                        self.is_running = True
                    elif 'GatewayPort-' in output_line:
                        self.gateway_port = int(output_line.strip().rsplit('GatewayPort-', 1)[-1])
                    elif output_line:
                        process_logger.info(output_line)
            else:
                time.sleep(1)
        logger.debug("Stdout exhausted. Closing gateway " + str(self.bootstrap_urls))
        self._cleanup()
