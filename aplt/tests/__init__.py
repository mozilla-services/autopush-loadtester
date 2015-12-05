from mock import Mock
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.trial import unittest


class TestIntegration(unittest.TestCase):
    def _check_done(self, d):
        d.callback(True)

    def testBasic(self):
        import aplt.runner as runner
        runner.RunnerHarness.reactor = Mock()
        runner.run_scenario({
            "<websocket_url>": "wss://autopush-dev.stage.mozaws.net/",
            "<scenario_function>": "aplt.scenarios:basic",
        })
        d = Deferred()
        reactor.callLater(15, self._check_done, d)
        return d
