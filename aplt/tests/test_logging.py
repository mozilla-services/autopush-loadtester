import os
import sys
import unittest
import io
import json
import time
from nose.tools import eq_

from twisted.logger import (
    formatEventAsClassicLogText
)
from twisted.logger._stdlib import StringifiableFromEvent

from aplt.logobserver import (
    AP_Logger,
    LogLevel

)


class TestLogger(unittest.TestCase):

    def test_init(self):
        obj = AP_Logger("test")
        eq_(obj._output, sys.stdout)
        eq_(obj.format_event, obj.json_format)

        filename = os.tempnam()
        fobj = AP_Logger("test", log_format="human",
                         log_output=filename)
        fobj.start()
        eq_(fobj._filename, filename)
        eq_(fobj.format_event, fobj.human_format)

        obj = AP_Logger("test", log_format="human", log_output="none")
        obj.start()
        eq_(obj._output, None)
        eq_(obj._filename, None)
        obj.stop()
        fobj.stop()

        obj = AP_Logger("test", log_format="unknown")
        eq_(obj.format_event, formatEventAsClassicLogText)

    def test_emit(self):
        buff = io.StringIO()
        obj = AP_Logger("test", log_level="error", log_output=buff)
        obj.emit({"log_level": LogLevel.info})
        obj.stop()

        obj = AP_Logger("test", log_format="json", log_output=buff)
        event = dict(format="%(log_legacy)",
                     log_namespace=u'log_legacy',
                     log_time=time.time(),
                     log_system='-',
                     log_legacy=StringifiableFromEvent,
                     log_level=LogLevel.info,
                     system='-',
                     time=time.time(),
                     log_text='Log opened.',
                     log_format=u'{log_text}',
                     message='Log opened.',
                     isError=0,
                     reason='some reason',
                     )
        obj.emit(event)
        buff.seek(0)
        out = json.loads(buff.read())
        eq_(out['log_level'], event['log_level'].name)
        eq_(out['message'], event['message'])
        eq_(out['isError'], event['isError'])
        eq_(out['reason'], event['reason'])
