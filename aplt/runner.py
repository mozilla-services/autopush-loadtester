"""Scenario Runner"""
import importlib
import sys
from collections import deque

import treq
from autobahn.twisted.websocket import (
    connectWS,
    WebSocketClientFactory
)
from docopt import docopt
from twisted.internet import reactor, ssl, task
from twisted.python import log

from aplt import __version__
from aplt.client import (
    CommandProcessor,
    WSClientProtocol
)


class RunnerHarness(object):
    """Runs multiple instances of a single scenario"""
    def __init__(self, websocket_url, scenario):
        self._factory = WebSocketClientFactory(
            websocket_url,
            headers={"Origin": "localhost:9000"},
            debug=False)
        self._factory.protocol = WSClientProtocol
        self._factory.protocol.harness = self
        if websocket_url.startswith("wss"):
            self._factory_context = ssl.ClientContextFactory()
        else:
            self._factory_context = None

        self._crypto_key = """\
keyid="http://example.org/bob/keys/123;salt="XZwpw6o37R-6qoZjw6KwAw"\
"""

        # Processor and Websocket client vars
        self._scenario = scenario
        self._processors = 0
        self._ws_clients = {}
        self._connect_waiters = deque()

    def run(self):
        """Start registered scenario"""
        # Create the processor and start it
        processor = CommandProcessor(self._scenario, self)
        processor.run()
        self._processors += 1

    def connect(self, processor):
        """Start a connection for a processor and queue it for when the
        connection is available"""
        connectWS(self._factory, contextFactory=self._factory_context)
        self._connect_waiters.append(processor)

    def send_notification(self, processor, url, data, ttl):
        """Send out a notification to a url for a processor"""
        url = url.encode("utf-8")
        if data:
            d = treq.post(
                url,
                data,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Encoding": "aesgcm-128",
                    "Encryption": self._crypto_key,
                    "Encryption-Key": "Invalid-Key-Used-Here",
                },
                allow_redirects=False)
        else:
            d = treq.post(url, allow_redirects=False)
        d.addCallback(self._sent_notification, processor)
        d.addErrback(self._error_notif, processor)

    def _sent_notification(self, result, processor):
        d = result.content()
        d.addCallback(self._finished_notification, result, processor)
        d.addErrback(self._error_notif, result, processor)

    def _finished_notification(self, result, response, processor):
        # Give the fully read content and response to the processor
        processor._send_command_result((response, result))

    def _error_notif(self, failure, processor):
        # Send the failure back
        processor._send_command_result((None, failure))

    def add_client(self, ws_client):
        """Register a new websocket connection and return a waiting
        processor"""
        try:
            processor = self._connect_waiters.popleft()
        except IndexError:
            log.msg("No waiting processors for new client connection.")
            ws_client.sendClose()
        else:
            self._ws_clients[ws_client] = processor
            return processor

    def remove_client(self, ws_client):
        """Remove a websocket connection from the client registry"""
        processor = self._ws_clients.pop(ws_client, None)
        if not processor:
            # Possible failed connection, if we have waiting processors still
            # then try a new connection
            if len(self._connect_waiters):
                connectWS(self._factory, contextFactory=self._factory_context)
            return

    def remove_processor(self):
        """Remove a completed processor"""
        self._processors -= 1


class LoadRunner(object):
        """Runs a bunch of scenarios for a load-test"""
        def __init__(self, scenario_list):
            """Initializes a LoadRunner

            Takes a list of tuples indicating scenario to run, quantity,
            stagger delay, and overall delay.

            Stagger delay is a number indicating how many of the scenario to
            launch per second.

            Overall delay is how many seconds after the start of the load-run
            before the scenario should begin.

            Example::

                lr = LoadRunner([
                    (basic, 1000, 100, 0),
                ])

            """
            self._harnesses = {}


def check_processors(harness):
    """Task to shut down the reactor if there are no processors running"""
    if not harness._processors:
        reactor.stop()


def run_scenario(args=None, run=True):
    """Run a scenario

    Usage:
        aplt_scenario <websocket_url> <scenario_function>

    """
    arguments = args or docopt(run_scenario.__doc__, version=__version__)
    arg = arguments["<scenario_function>"]
    if ":" not in arg:
        raise Exception("Missing function designation")
    mod, func_name = arg.split(":")
    module = importlib.import_module(mod)
    scenario = getattr(module, func_name)
    log.startLogging(sys.stdout)
    h = RunnerHarness(arguments["<websocket_url>"], scenario)
    h.run()

    if run:
        l = task.LoopingCall(check_processors, h)
        l.start(1.0)
        reactor.run()
    else:
        return h
