import sys
import unittest
import io
import json
import time
import tempfile

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
        assert obj._output == sys.stdout
        assert obj.format_event == obj.json_format

        filename = tempfile.NamedTemporaryFile().name
        fobj = AP_Logger("test", log_format="human",
                         log_output=filename)
        fobj.start()
        assert fobj._filename == filename
        assert fobj.format_event == fobj.human_format

        obj = AP_Logger("test", log_format="human", log_output="none")
        obj.start()
        assert obj._output is None
        assert obj._filename is None
        obj.stop()
        fobj.stop()

        obj = AP_Logger("test", log_format="human", log_output="stdout")
        obj.start()
        assert obj._output == sys.stdout
        assert obj._filename is None
        obj.stop()
        fobj.stop()

        obj = AP_Logger("test", log_format="unknown")
        assert obj.format_event == formatEventAsClassicLogText

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
                     reason=dict(cause='some reason'),
                     )
        obj.emit(event)
        buff.seek(0)
        out = json.loads(buff.read())
        assert out['log_level'] == event['log_level'].name
        assert out['message'] == event['message']
        assert out['isError'] == event['isError']
        assert out['reason'] == repr(event['reason'])
