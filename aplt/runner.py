"""Scenario Runner"""
import logging
import importlib
import inspect
import json
import re
import urlparse
from collections import deque
from StringIO import StringIO

import treq
from autobahn.twisted.websocket import (
    connectWS,
    WebSocketClientFactory
)
from configargparse import ArgumentParser
from twisted.internet import reactor, ssl, task
from twisted.python import log
from twisted.web.client import Agent

import aplt.metrics as metrics
from aplt.client import (
    CommandProcessor,
    WSClientProtocol
)
from aplt.utils import UnverifiedHTTPS
from aplt.vapid import Vapid
from aplt.logobserver import AP_Logger


# Necessary for latest version of txaio
import txaio
txaio.use_twisted()

STATS_PROTOCOL = None

PEM_FILE_HEADER = "-----BEGIN "


class RunnerHarness(object):
    """Runs multiple instances of a single scenario

    Running an instance of the scenario is triggered with :meth:`run`. It
    will run to completion or possibly forever.

    """
    def __init__(self,
                 load_runner,
                 websocket_url,
                 statsd_client,
                 scenario,
                 endpoint=None,
                 endpoint_ssl_cert=None,
                 endpoint_ssl_key=None,
                 *scenario_args,
                 **scenario_kw):
        self._factory = WebSocketClientFactory(
            websocket_url,
            headers={"Origin": "http://localhost:9000"})
        self._factory.protocol = WSClientProtocol
        self._factory.harness = self
        if websocket_url.startswith("wss"):
            self._factory_context = ssl.ClientContextFactory()
        else:
            self._factory_context = None

        # somewhat bogus encryption headers
        self._crypto_key = "keyid=p256dh;dh=c2VuZGVy"
        self._encryption = "keyid=p256dh;salt=XZwpw6o37R-6qoZjw6KwAw"

        # Processor and Websocket client vars
        self._scenario = scenario
        self._scenario_args = scenario_args
        self._scenario_kw = scenario_kw
        self._processors = 0
        self._ws_clients = {}
        self._connect_waiters = deque()
        self._load_runner = load_runner
        self._stat_client = statsd_client
        self._vapid = Vapid()
        if "vapid_private_key" in self._scenario_kw:
            self._vapid = Vapid(
                private_key=self._scenario_kw.get(
                    "vapid_private_key"))
        else:
            self._vapid.generate_keys()
        self._claims = ()
        if "vapid_claims" in self._scenario_kw:
            self._claims = self._scenario_kw.get("vapid_claims")

        self._endpoint = urlparse.urlparse(endpoint) if endpoint else None
        self._agent = None
        if endpoint_ssl_cert:
            self._agent = Agent(
                reactor,
                contextFactory=UnverifiedHTTPS(
                    endpoint_ssl_cert,
                    endpoint_ssl_key))
            if hasattr(endpoint_ssl_cert, 'seek'):
                endpoint_ssl_cert.seek(0)
            if endpoint_ssl_key and hasattr(endpoint_ssl_key, 'seek'):
                endpoint_ssl_key.seek(0)

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

    def send_notification(self, processor, url, data, ttl, claims=None):
        """Send out a notification to a url for a processor

        This uses the older `aesgcm` format.

        """
        url = url.encode("utf-8")
        headers = {"TTL": str(ttl)}
        crypto_key = self._crypto_key
        if claims is None:
            claims = ()
        claims = claims or self._claims
        if self._vapid and claims:
            if "aud" not in claims:
                # Construct a valid `aud` from the known endpoint
                parsed = urlparse.urlparse(url)
                claims["aud"] = "{scheme}://{netloc}".format(
                    scheme=parsed.scheme,
                    netloc=parsed.netloc
                )
                log.msg("Setting VAPID 'aud' to {}".format(claims["aud"]))
            headers.update(self._vapid.sign(claims))
            crypto_key = "{};p256ecdsa={}".format(
                crypto_key,
                self._vapid.public_key_urlsafe_base64
            )
        if data:
            headers.update({
                "Content-Type": "application/octet-stream",
                "Content-Encoding": "aesgcm",
                "Crypto-key": crypto_key,
                "Encryption": self._encryption,
            })

        d = treq.post(url,
                      data=data,
                      headers=headers,
                      allow_redirects=False,
                      agent=self._agent)
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
        def __init__(self,
                     scenario_list,
                     statsd_client,
                     websocket_url,
                     endpoint,
                     endpoint_ssl_cert,
                     endpoint_ssl_key):
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
            self._endpoint = endpoint
            self._endpoint_ssl_cert = endpoint_ssl_cert
            self._endpoint_ssl_key = endpoint_ssl_key

        def start(self):
            """Schedules all the scenarios supplied"""
            for testplan in self._testplans:
                self._run_testplan(testplan)
            self._started = True

        def _run_testplan(self, test_plan):
            scenario, quantity, stagger, overall_delay, scenario_args = \
                test_plan
            harness = RunnerHarness(
                self,
                self._websocket_url,
                self._statsd_client,
                scenario,
                self._endpoint,
                self._endpoint_ssl_cert,
                self._endpoint_ssl_key,
                *scenario_args[0],
                **scenario_args[1]
            )
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
            calls it queued, and all the processors have finished.

            Processes in an error state may return -1, which can cause this to
            endlessly loop.

            """
            return all([
                self._started,
                self._queued_calls == 0,
                all([x._processors <= 0 for x in self._harnesses])
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
    if ":" in func_name:
        module_path, object_path = func_name.split(":")
    else:
        module_path = "aplt.scenarios"
        object_path = func_name
    scenario = importlib.import_module(module_path)
    for bit in object_path.split("."):
        scenario = getattr(scenario, bit)
    return scenario


def verify_arguments(func, *func_args, **func_kwargs):
    """Verify that a function can be called with the arguments supplied"""
    args, varargs, keywords, defaults = inspect.getargspec(func)
    arg_len = len(func_args)

    # If its a class method, one less required args
    if hasattr(func, "__self__") and func.__self__ is not None:
        args = args[1:]

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
        except (ValueError, TypeError):
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
        # command line args come in as strings.
        int_args, kw_args = group_kw_args(parts)
        int_args = try_int_list_coerce(int_args)
        func_args = int_args[3:]
        verify_arguments(func, *func_args, **kw_args)
        args = [func] + int_args[:3]
        args.append((func_args, kw_args))
        result.append(tuple(args))
    return result


def parse_string_to_list(string):
    """Parse a string into a list of strings"""
    if string:
        string = re.sub("(?<!\\\\),", "\0", string)
        items = [x.strip() for x in string.strip().split("\0")]
        return items
    else:
        return []


def parse_statsd_args(args=None):
    """Parses statsd args out of a docopt arguments dict and returns a statsd
    client or None"""
    if args is None:
        return metrics.SinkMetrics()
    if args.statsd_host is not None:
        # We're using statsd
        return metrics.TwistedMetrics(args.statsd_host,
                                      args.statsd_port,
                                      args.metric_namespace)
    elif args.datadog_api_key is not None:
        # We're using datadog
        return metrics.DatadogMetrics(
            api_key=args.datadog_api_key,
            app_key=args.datadog_app_key,
            flush_interval=args.datadog_flush_interval,
            namespace=args.metric_namespace
        )
    else:
        # Metric sink
        return metrics.SinkMetrics()


def parse_endpoint_args(args):
    endpoint = args.endpoint
    if endpoint:
        url = urlparse.urlparse(endpoint)
        if (not (url.scheme or url.netloc) or
                any(c != '/' for c in url.path) or
                any(url[3:])):
            raise Exception("Invalid endpoint: " + endpoint)
    cert = args.endpoint_ssl_cert
    key = args.endpoint_ssl_key
    if cert:
        if cert.startswith(PEM_FILE_HEADER):
            cert = StringIO(cert)
        if key.startswith(PEM_FILE_HEADER):
            key = StringIO(cert)
    return endpoint, cert, key


def group_kw_args(*args):
    """Divvy up argument hashes and single values into args and kwargs."""
    kw_args = {}
    argList = []
    if not args:
        return argList, kw_args

    # args may be a json encoded block:
    for arg in args:
        try:
            items = json.loads(arg)
            if isinstance(items, dict):
                kw_args.update(json.loads(arg))
            if isinstance(items, list):
                argList.extend(items)
            continue
        except (ValueError, TypeError):
            pass  # probably not JSON, so move on.
        if isinstance(arg, list):
            argList.extend(arg)
            continue
        if isinstance(arg, dict):
            kw_args.update(arg)
            continue
    return argList, kw_args


def val_to_level(val):
    try:
        val = logging._checkLevel(val)
        val = int(round(val/10)) * 10
    except (ValueError, TypeError):
        val = logging.INFO
    return val


def parse_common_args(parser):
    """Shared arguments for `run_scenario` and `run_testplan`"""
    parser.add_argument("-u", "--websocket_url",
                        help="Websocket URL path",
                        type=str,
                        default="wss://push.services.mozilla.com")
    parser.add_argument("--metric_namespace",
                        help="namespace for metric collection",
                        env_var="METRIC_NAMESPACE",
                        default="push_test")
    parser.add_argument("--statsd_host",
                        help="host for metric collection",
                        env_var="STATSD_HOST")
    parser.add_argument("--statsd_port",
                        default=8125,
                        type=int,
                        help="port on statsd_host for metric collection",
                        env_var="STATSD_PORT")
    parser.add_argument("--datadog_api_key",
                        help="datadog API key",
                        env_var="DATADOG_API_KEY")
    parser.add_argument("--datadog_app_key",
                        help="datadog application key",
                        env_var="DATADOG_APP_KEY")
    parser.add_argument("--datadog_flush_interval",
                        type=int,
                        help="period (in secs) before datadog data flushed",
                        env_var="DATADOG_FLUSH_INTERVAL")
    parser.add_argument("-e", "--endpoint",
                        help="push notification endpoint override URL",
                        env_var="ENDPOINT")
    parser.add_argument("--endpoint_ssl_cert",
                        help="path to custom TLS cert for endpoint",
                        env_var="ENDPOINT_SSL_CERT")
    parser.add_argument("--endpoint_ssl_key",
                        help="path to custom TLS key for endpoint",
                        env_var="ENDPOINT_SSL_KEY")
    parser.add_argument("--log_name",
                        help="log prefix name",
                        env_var="LOG_NAME",
                        default="push_test")
    parser.add_argument("--log_level",
                        help="minimum log level to report (debug, info, warn,"
                             "error, critical)",
                        env_var="LOG_LEVEL",
                        default="info")
    parser.add_argument("--log_format",
                        help="format for log output (default, human, json)",
                        env_var="LOG_FORMAT",
                        default="default")
    parser.add_argument("--log_output",
                        help="output target for log info (stdout, none, path)",
                        default="stdout",
                        env_var="LOG_OUTPUT")


def parse_scenario_args(args):
    parser = ArgumentParser(
        description="Run a scenario",
        default_config_files=["config.ini"],
        args_for_setting_config_path=["-c", "--config"],
    )
    parse_common_args(parser)
    parser.add_argument("scenario")
    parser.add_argument("scenario_args", nargs="*",
                        help="Arguments for the specific scenario")
    return parser.parse_args(args)


def run_scenario(args=None, run=True):
    """Run a scenario

    Usage:
        aplt_scenario SCENARIO_FUNCTION [WEBSOCKET_URL] [SCENARIO_ARGS ...]
                      [--metric_namespace=METRIC_NAMESPACE]
                      [--statsd_host=STATSD_HOST]
                      [--statsd_port=STATSD_PORT]
                      [--datadog_api_key=DD_API_KEY]
                      [--datadog_app_key=DD_APP_KEY]
                      [--datadog_flush_interval=DD_FLUSH_INTERVAL]
                      [-e URL --endpoint=URL]
                      [--endpoint_ssl_cert=SSL_CERT]
                      [--endpoint_ssl_key=SSL_KEY]
                      [--log_level=LOG_LEVEL]
                      [--log_format=LOG_FORMAT]
                      [--log_output=LOG_OUTPUT]

    Other environment variables:
    ENDPOINT_SSL_CERT: like --endpoint_ssl_cert, but see below
    ENDPOINT_SSL_KEY:  like --endpoint_ssl_key, but see below

    The ENDPOINT_SSL_CERT/ENDPOINT_SSL_KEY environment variables
    accept a path to cert files (like the command line equivalent) or
    optionally the contents of the PEM files themselves.

    """

    arguments = parse_scenario_args(args)
    # set some reasonable defaults.
    arg = arguments.scenario
    scenario = locate_function(arg)
    statsd_client = parse_statsd_args(arguments)
    scenario_args = []
    scenario_kw = {}
    if arguments.scenario_args:
        scenario_args, scenario_kw = group_kw_args(arguments.scenario_args)
        scenario_args = try_int_list_coerce(scenario_args)
        verify_arguments(scenario, *scenario_args, **scenario_kw)
    endpoint, ssl_cert, ssl_key = parse_endpoint_args(arguments)

    # this is a smoke test, so only run one instance once.
    plan = ([scenario, 1, 1, 0] + [(scenario_args, scenario_kw)])
    testplans = [plan]

    lh = LoadRunner(testplans, statsd_client, arguments.websocket_url,
                    endpoint, ssl_cert, ssl_key)
    if arguments.log_format:
        observer = AP_Logger(arguments.log_name,
                             arguments.log_level,
                             arguments.log_format,
                             arguments.log_output)
        observer.start()
    else:
        observer = log.PythonLoggingObserver()
    log.startLoggingWithObserver(observer.emit, False)
    logging.basicConfig(level=val_to_level(arguments.log_level))
    statsd_client.start()
    lh.metrics = statsd_client
    lh.start()

    if run:
        l = task.LoopingCall(check_loadrunner, lh)
        reactor.callLater(1, l.start, 1)
        reactor.run()
    else:
        return lh

    if isinstance(observer, AP_Logger):
        observer.stop()


def parse_testplan_args(args):
    parser = ArgumentParser(
        description="Run a scenario",
        default_config_files=["config.ini"],
        args_for_setting_config_path=["-c", "--config"],
    )
    parse_common_args(parser)
    parser.add_argument("test_plan")
    return parser.parse_args(args)


def run_testplan(args=None, run=True):
    """Run a testplan

    Usage:
        aplt_testplan TEST_PLAN WEBSOCKET_URL
                      [--metric_namespace=METRIC_NAMESPACE]
                      [--statsd_host=STATSD_HOST]
                      [--statsd_port=STATSD_PORT]
                      [--datadog_api_key=DD_API_KEY]
                      [--datadog_app_key=DD_APP_KEY]
                      [--datadog_flush_interval=DD_FLUSH_INTERVAL]
                      [--endpoint=URL]
                      [--endpoint_ssl_cert=SSL_CERT]
                      [--endpoint_ssl_key=SSL_KEY]

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

    Other environment variables:
    ENDPOINT_SSL_CERT: like --endpoint_ssl_cert, but see below
    ENDPOINT_SSL_KEY:  like --endpoint_ssl_key, but see below

    The ENDPOINT_SSL_CERT/ENDPOINT_SSL_KEY environment variables
    accept a path to cert files (like the command line equivalent) or
    optionally the contents of the PEM files themselves.

    """
    arguments = parse_testplan_args(args)
    testplans = parse_testplan(arguments.test_plan)
    statsd_client = parse_statsd_args(arguments)
    endpoint, ssl_cert, ssl_key = parse_endpoint_args(arguments)
    lh = LoadRunner(testplans, statsd_client, arguments.websocket_url,
                    endpoint, ssl_cert, ssl_key)
    observer = log.PythonLoggingObserver()
    log.startLoggingWithObserver(observer.emit, False)
    logging.basicConfig(level=logging.INFO)
    statsd_client.start()
    lh.metrics = statsd_client
    lh.start()

    if run:
        l = task.LoopingCall(check_loadrunner, lh)
        reactor.callLater(1, l.start, 1)
        reactor.run()
    else:
        return lh
