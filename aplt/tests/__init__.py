from mock import Mock, patch
from nose.tools import eq_
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.trial import unittest


class TestIntegration(unittest.TestCase):
    def _check_done(self, harness, d):
        if not harness._processors:
            d.callback(True)
        else:
            reactor.callLater(0.5, self._check_done, harness, d)

    def _check_testplan_done(self, load_runner, d):
        if load_runner.finished:
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
        import aplt.runner as runner
        h = runner.run_scenario({
            "WEBSOCKET_URL": "wss://autopush-dev.stage.mozaws.net/",
            "SCENARIO_FUNCTION": "aplt.scenarios:basic",
        }, run=False)
        d = Deferred()
        reactor.callLater(0.5, self._check_done, h, d)
        return d

    def test_basic_testplan(self):
        import aplt.runner as runner
        lh = runner.run_testplan({
            "WEBSOCKET_URL": "wss://autopush-dev.stage.mozaws.net/",
            "TEST_PLAN": "aplt.scenarios:basic, 5, 5, 0",
        }, run=False)
        d = Deferred()
        reactor.callLater(0.5, self._check_testplan_done, lh, d)
        return d

    def test_bad_load(self):
        import aplt.runner as runner
        self.assertRaises(Exception, runner.run_scenario, {
            "WEBSOCKET_URL": "wss://autopush-dev.stage.mozaws.net/",
            "SCENARIO_FUNCTION": "aplt.scenaribasic",
        }, run=False)


class TestHarness(unittest.TestCase):
    def _make_harness(self):
        from aplt.runner import RunnerHarness
        from aplt.scenarios import basic
        return RunnerHarness("wss://autopush-dev.stage.mozaws.net/", basic)

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
