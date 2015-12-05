from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.trial import unittest


class TestIntegration(unittest.TestCase):
    def _check_done(self, harness, d):
        if not harness._processors:
            d.callback(True)
        else:
            reactor.callLater(0.5, self._check_done, harness, d)

    def tearDown(self):
        # Find the connection pool and shut it down
        from treq._utils import get_global_pool
        pool = get_global_pool()
        return pool.closeCachedConnections()

    def testBasic(self):
        import aplt.runner as runner
        h = runner.run_scenario({
            "<websocket_url>": "wss://autopush-dev.stage.mozaws.net/",
            "<scenario_function>": "aplt.scenarios:basic",
        }, run=False)
        d = Deferred()
        reactor.callLater(0.5, self._check_done, h, d)
        return d
