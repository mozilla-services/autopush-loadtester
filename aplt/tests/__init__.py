import json
import time

from mock import Mock, patch
from nose.tools import eq_, raises
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.trial import unittest


AUTOPUSH_SERVER = "wss://autopush.dev.mozaws.net/"


def _wait_multiple():
    from aplt.commands import wait
    yield wait(0.1)
    yield wait(0.1)
    yield wait(0.1)


def _stack_gens():
    from aplt.commands import wait
    yield _wait_multiple()
    yield wait(0.1)


class Aclass(object):
    @classmethod
    def amethod(cls):
        yield _wait_multiple()


class TestIntegration(unittest.TestCase):
    def _check_testplan_done(self, load_runner, d):
        if load_runner.finished:
            load_runner.metrics.stop()
            d.callback(True)
        else:
            reactor.callLater(0.5, self._check_testplan_done, load_runner, d)

    def tearDown(self):
        # Find the connection pool and shut it down
        from treq._utils import get_global_pool
        pool = get_global_pool()
        if pool:
            return pool.closeCachedConnections()

    def test_basic_runner(self):
        """Test the "basic" scenario.

        This can be called via pytest using
        `bin/pytest aplt/tests/__init__.py::TestIntegration::test_basic_runner`

        Use `check_log` to examine the produced log file for whatever values
        you need.

        """  # pragma noqa
        import aplt.runner as runner
        h = runner.run_scenario([
            "--log_format=json",
            "--log_output=buffer",  # send the output to a string buffer
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:basic",
        ], run=False)

        def check_log(success):
            """Check the captured output log for whatever content your
            looking for

            """
            dump = h.logging.dump()
            assert len(dump) > 0
            # Additional checks here...

        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, h, d)
        d.addCallback(check_log)
        return d

    def test_basic_with_vapid(self):
        import aplt.runner as runner
        h = runner.run_scenario([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:basic",
            """vapid_claims={"sub": "mailto:admin@example.com"}""",
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, h, d)
        return d

    def test_basic_with_vapid_str_args(self):
        """Test common format for command line arguments

        Command line tests should escape commas in the keyword args,
        e.g.

        ```
        ARGS='{"vapid_private_key":"MHc..."\\,"vapid_claims":{...}}'
        aplt_testplan $HOST "aplt.scenarios:basic,1,1,0,$ARGS"
        ```

        """
        import aplt.runner as runner
        from aplt.tests.test_vapid import T_PRIVATE
        claims = {"aud": "https://example.com",
                  "sub": "mailto:admin@example.com",
                  "exp": int(time.time()) + 86400}
        args = {"vapid_private_key": T_PRIVATE,
                "vapid_claims": claims}
        jclaims = json.dumps(args).replace(",", "\\,")
        h = runner.run_scenario([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:basic",
            jclaims,
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, h, d)
        return d

    def test_basic_testplan(self):
        import aplt.runner as runner
        lh = runner.run_testplan([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:basic, 5, 5, 0",
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, lh, d)
        return d

    def test_spawn_testplan(self):
        import aplt.runner as runner
        h = runner.run_scenario([
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:_test_spawn",
        ], run=False)
        d = Deferred()
        reactor.callLater(3, self._check_testplan_done, h, d)
        return d

    def test_spawn_multiple_testplan(self):
        import aplt.runner as runner
        h = runner.run_scenario([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:_test_multiple_spawn",
        ], run=False)
        d = Deferred()
        reactor.callLater(3, self._check_testplan_done, h, d)
        return d

    def test_basic_testplan_with_args(self):
        import aplt.runner as runner
        lh = runner.run_testplan([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:notification_forever, 5, 5, 0, 1, 1",
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, lh, d)
        return d

    def test_wait_twice(self):
        import aplt.runner as runner
        lh = runner.run_testplan([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.tests:_wait_multiple, 1, 1, 0",
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, lh, d)
        return d

    def test_stack_gens(self):
        import aplt.runner as runner
        lh = runner.run_testplan([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.tests:_stack_gens, 1, 1, 0",
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, lh, d)
        return d

    def test_class_method(self):
        import aplt.runner as runner
        lh = runner.run_testplan([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.tests:Aclass.amethod, 1, 1, 0",
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, lh, d)
        return d

    @raises(Exception)
    def test_bad_testplan(self):
        import aplt.runner as runner
        runner.run_testplan([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:basic, 5, 5",
        ], run=False)

    @raises(Exception)
    def test_bad_load(self):
        import aplt.runner as runner
        runner.run_scenario([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenaribasic",
        ], run=False)

    def test_notification_forever(self):
        import aplt.runner as runner
        h = runner.run_scenario([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:notification_forever",
            '0', '1',
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, h, d)
        return d

    def test_reconnect_forever(self):
        import aplt.runner as runner

        h = runner.run_scenario([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:reconnect_forever",
            '0', '1',  # args are broken into a list by parser.
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, h, d)
        return d

    def test_expect_notifications(self):
        import aplt.runner as runner
        h = runner.run_scenario([
            "aplt.scenarios:_expect_notifications",
            AUTOPUSH_SERVER,
            "--log_output=none",
        ], run=False)
        d = Deferred()
        reactor.callLater(0, self._check_testplan_done, h, d)
        return d

    def test_exception_restart(self):
        import aplt.runner as runner
        import aplt.scenarios as scenarios
        scenarios._RESTARTS = 0
        h = runner.run_scenario([
            "--log_output=none",
            "--websocket_url={}".format(AUTOPUSH_SERVER),
            "aplt.scenarios:_explode",
        ], run=False)
        f = Deferred()
        d = Deferred()
        eq_(scenarios._RESTARTS, 0)

        def check_restarts(result):
            self.flushLoggedErrors()
            eq_(scenarios._RESTARTS, 3)
            f.callback(True)
        d.addBoth(check_restarts)
        reactor.callLater(0, self._check_testplan_done, h, d)
        return f


class TestHarness(unittest.TestCase):
    def _make_harness(self):
        from aplt.runner import RunnerHarness, parse_statsd_args
        from aplt.scenarios import basic
        client = parse_statsd_args()
        self.rh = RunnerHarness(Mock(), AUTOPUSH_SERVER, basic, client)
        self.rh.metrics = client
        return self.rh

    def tearDown(self):
        if hasattr(self, "rh"):
            self.rh.metrics.stop()

    def test_no_waiting_processors(self):
        h = self._make_harness()
        mock_client = Mock()
        h.add_client(mock_client)
        eq_(mock_client.sendClose.called, True)

    @patch("aplt.runner.connectWS")
    def test_remove_client_with_waiting_processors(self, mock_connect):
        h = self._make_harness()
        h._connect_waiters.append(Mock())
        mock_client = Mock()
        h.remove_client(mock_client)
        eq_(mock_connect.called, True)


class TestRunnerFunctions(unittest.TestCase):
    @raises(Exception)
    def test_verify_func_too_many_args(self):
        from aplt.runner import verify_arguments
        from aplt.scenarios import connect_and_idle_forever
        verify_arguments(connect_and_idle_forever, 0, 0, "extra_arg")

    @raises(Exception)
    def test_verify_func_short_an_arg(self):
        from aplt.runner import verify_arguments

        def needsanarg(some_arg):  # pragma: nocover
            print some_arg

        verify_arguments(needsanarg)

    def test_verify_func_kwargs(self):
        from aplt.runner import verify_arguments

        def extras(*theargs):  # pragma: nocover
            print theargs

        result = verify_arguments(extras, 1, 2, 3, 4, 5)
        eq_(result, True)
