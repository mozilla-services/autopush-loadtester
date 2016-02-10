"""Scenario Runner"""
import importlib
import inspect
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
import aplt.metrics as metrics

# Necessary for latest version of txaio
import txaio
txaio.use_twisted()

STATS_PROTOCOL = None


class RunnerHarness(object):
    """Runs multiple instances of a single scenario

    Running an instance of the scenario is triggered with :meth:`run`. It
    will run to completion or possibly forever.

    """
    def __init__(self, load_runner, websocket_url, statsd_client, scenario,
                 *scenario_args):
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
        self._scenario_args = scenario_args
        self._processors = 0
        self._ws_clients = {}
        self._connect_waiters = deque()
        self._load_runner = load_runner
        self._stat_client = statsd_client

    def run(self):
        """Start registered scenario"""
        # Create the processor and start it
        processor = CommandProcessor(self._scenario, self._scenario_args, self)
        processor.run()
        self._processors += 1

    def spawn(self, test_plan):
        """Spawn a new test plan"""
        self._load_runner.spawn(test_plan)

    def connect(self, processor):
        """Start a connection for a processor and queue it for when the
        connection is available"""
        self._connect_waiters.append(processor)
        connectWS(self._factory, contextFactory=self._factory_context)

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
                    "TTL": str(ttl),
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

    def timer(self, name, duration):
        """Record a metric timer if we have a statsd client"""
        self._stat_client.timing(name, duration)

    def counter(self, name, count=1):
        """Record a counter if we have a statsd client"""
        self._stat_client.increment(name, count)


class LoadRunner(object):
        """Runs a bunch of scenarios for a load-test"""
        def __init__(self, scenario_list, statsd_client, websocket_url):
            """Initializes a LoadRunner

            Takes a list of tuples indicating scenario to run, quantity,
            stagger delay, and overall delay.

            Stagger delay is a number indicating how many of the scenario to
            launch per second.

            Overall delay is how many seconds after the start of the load-run
            before the scenario should begin.

            Example::

                lr = LoadRunner([
                    (basic, 1000, 100, 0, *scenario_args),
                ], "wss://somepushservice/")

            .. note::

                Any leftover quantity not cleanly divided into the stagger
                delay will not be started. The quantity should be cleanly
                divided into stagger delay.

            """
            self._harnesses = []
            self._testplans = scenario_list
            self._started = False
            self._queued_calls = 0
            self._statsd_client = statsd_client
            self._websocket_url = websocket_url

        def start(self):
            """Schedules all the scenarios supplied"""
            for testplan in self._testplans:
                self._run_testplan(testplan)
            self._started = True

        def _run_testplan(self, test_plan):
            scenario, quantity, stagger, overall_delay, scenario_args = \
                test_plan
            harness = RunnerHarness(self, self._websocket_url,
                                    self._statsd_client, scenario,
                                    *scenario_args)
            self._harnesses.append(harness)
            iterations = quantity / stagger
            for delay in range(iterations):
                def runall():
                    for _ in range(stagger):
                        harness.run()
                    self._queued_calls -= 1
                self._queued_calls += 1
                reactor.callLater(overall_delay+delay, runall)

        @property
        def finished(self):
            """Indicates whether or not the LoadRunner started, has run all the
            calls it queued, and all the processors have finished"""
            return all([
                self._started,
                self._queued_calls == 0,
                all([x._processors == 0 for x in self._harnesses])
            ])

        def spawn(self, test_plan):
            """Spawn a new test plan"""
            testplans = parse_testplan(test_plan)
            self._run_testplan(testplans[0])


def check_processors(harness):
    """Task to shut down the reactor if there are no processors running"""
    if harness._processors == 0:
        harness.metrics.stop()
        reactor.stop()


def check_loadrunner(load_runner):
    """Task to shut down the reactor when the load runner has finished"""
    if load_runner.finished:
        load_runner.metrics.stop()
        reactor.stop()


def locate_function(func_name):
    """Locates and loads a function by the string name similar to an entry
    points

    Format of func_name: <package/module>:<function>

    """
    if ":" not in func_name:
        raise Exception("Missing function designation")
    mod, func_name = func_name.split(":")
    module = importlib.import_module(mod)
    scenario = getattr(module, func_name)
    return scenario


def verify_arguments(func, *func_args):
    """Verify that a function can be called with the arguments supplied"""
    args, varargs, keywords, defaults = inspect.getargspec(func)
    arg_len = len(func_args)

    # First, check the minimum required arg length
    defaults = defaults or []
    min_arg_len = len(args) - len(defaults)
    if arg_len < min_arg_len:
        raise Exception("%s takes minimum of %s args, %s supplied." % (
                        func, min_arg_len, arg_len))

    # Met the min args, if the function has * it can handle anything else
    if varargs:
        return True

    # Finally, check for inability to call function with so many args
    if arg_len > len(args):
        raise Exception("%s takes maximum of %s args, %s supplied." % (
                        func, len(args), arg_len))


def try_int_list_coerce(lst):
    """Attempt to coerce all the elements of a list to ints and return it"""
    new_lst = []
    for p in lst:
        try:
            new_lst.append(int(p))
        except ValueError:
            new_lst.append(p)
    return new_lst


def parse_testplan(testplan):
    """Parse a test plan string into an array of tuples"""
    plans = testplan.split("|")
    result = []
    for plan in plans:
        parts = parse_string_to_list(plan)
        func_name = parts.pop(0)
        if len(parts) < 3:
            raise Exception("Error parsing test plan. Plan for %s needs 3 "
                            "arguments, only got: %s" % (func_name, parts))
        func = locate_function(func_name)
        int_args = try_int_list_coerce(parts)
        func_args = int_args[3:]
        verify_arguments(func, *func_args)
        args = [func] + int_args[:3]
        args.append(tuple(func_args))
        result.append(tuple(args))
    return result


def parse_string_to_list(string):
    """Parse a string into a list of strings"""
    if string:
        return [x.strip() for x in string.strip().split(",")]
    else:
        return []


def parse_statsd_args(args):
    """Parses statsd args out of a docopt arguments dict and returns a statsd
    client or None"""
    namespace = args.get("--metric_namespace") or "push_test"
    if args.get("--statsd_host"):
        # We're using statsd
        host = args.get("--statsd_host")
        port = int(args.get("--statsd_port") or 8125)
        return metrics.TwistedMetrics(host, port, namespace)
    elif args.get("--datadog_api_key"):
        # We're using datadog
        return metrics.DatadogMetrics(
            api_key=args.get("--datadog_api_key"),
            app_key=args.get("--datadog_app_key"),
            flush_interval=args.get("--datadog_flush_interval"),
            namespace=namespace
        )
    else:
        # Metric sink
        return metrics.SinkMetrics()


def run_scenario(args=None, run=True):
    """Run a scenario

    Usage:
        aplt_scenario WEBSOCKET_URL SCENARIO_FUNCTION [SCENARIO_ARGS ...]
                      [--metric_namespace=METRIC_NAMESPACE]
                      [--statsd_host=STATSD_HOST]
                      [--statsd_port=STATSD_PORT]
                      [--datadog_api_key=DD_API_KEY]
                      [--datadog_app_key=DD_APP_KEY]
                      [--datadog_flush_interval=DD_FLUSH_INTERVAL]

    """
    arguments = args or docopt(run_scenario.__doc__, version=__version__)
    arg = arguments["SCENARIO_FUNCTION"]
    scenario = locate_function(arg)
    log.startLogging(sys.stdout)
    statsd_client = parse_statsd_args(arguments)
    scenario_args = try_int_list_coerce(arguments["SCENARIO_ARGS"])
    verify_arguments(scenario, *scenario_args)

    plan = tuple([scenario, 1, 1, 0] + [tuple(scenario_args)])
    testplans = [plan]

    lh = LoadRunner(testplans, statsd_client, arguments["WEBSOCKET_URL"])
    log.startLogging(sys.stdout)
    statsd_client.start()
    lh.metrics = statsd_client
    lh.start()

    if run:
        l = task.LoopingCall(check_loadrunner, lh)
        reactor.callLater(1, l.start, 1)
        reactor.run()
    else:
        return lh


def run_testplan(args=None, run=True):
    """Run a testplan

    Usage:
        aplt_testplan WEBSOCKET_URL TEST_PLAN
                      [--metric_namespace=METRIC_NAMESPACE]
                      [--statsd_host=STATSD_HOST]
                      [--statsd_port=STATSD_PORT]
                      [--datadog_api_key=DD_API_KEY]
                      [--datadog_app_key=DD_APP_KEY]
                      [--datadog_flush_interval=DD_FLUSH_INTERVAL]

    test_plan should be a string with the following format:
        "<scenario_function>, <quantity>, <stagger>, <delay>, *args | *repeat"

    scenario_function
        String indicating function for the scenario, ex: aplt.scenarios:basic

    quantity
        Integer quantity of instances of the scenario to launch

    stagger
        How many to launch per second up to <quantity> total

    delay
        How long to wait from when the test begins before this portion runs

    *args
        Any optional additional arguments to be supplied to the scenario. The
        argument will be coerced to an integer if possible.

    *repeat
        More tuples of the same format.

    """
    arguments = args or docopt(run_testplan.__doc__, version=__version__)
    testplans = parse_testplan(arguments["TEST_PLAN"])
    statsd_client = parse_statsd_args(arguments)
    lh = LoadRunner(testplans, statsd_client, arguments["WEBSOCKET_URL"])
    log.startLogging(sys.stdout)
    statsd_client.start()
    lh.metrics = statsd_client
    lh.start()

    if run:
        l = task.LoopingCall(check_loadrunner, lh)
        reactor.callLater(1, l.start, 1)
        reactor.run()
    else:
        return lh
