import io
import json
import sys
import time

from twisted.logger import (
    formatEventAsClassicLogText,
    formatEvent,
    LogLevel,
    ILogObserver,
    globalLogBeginner,
    globalLogPublisher

)

from zope.interface import implementer

began_logging = False


def begin_or_register(observer, redirectStandardIO=False, **kwargs):
    global began_logging

    if not began_logging:
        globalLogBeginner.beginLoggingTo(
            [observer],
            redirectStandardIO=redirectStandardIO,
            **kwargs
        )
        began_logging = True
    else:
        globalLogPublisher.addObserver(observer=observer)  # pragma nocover


def stop(observer):
    globalLogPublisher.removeObserver(observer=observer)  # pragma nocover


@implementer(ILogObserver)
class AP_Logger(object):

    def __init__(self, logger_name, log_level="debug",
                 log_format="json", log_output="stdout"):
        self._start = time.time()
        self.logger_name = logger_name
        self._filename = None
        self._log_level = LogLevel.lookupByName(log_level)
        self._output = None
        if not isinstance(log_output, str):
            self._output = log_output
        else:
            if log_output.lower() == "none":
                self.format_event = self.null_format
                return
            if log_output.lower() == "stdout":
                self._output = sys.stdout
            if log_output.lower() == "buffer":
                self._output = io.StringIO()
            else:
                self._filename = log_output
        try:
            self.format_event = getattr(self, "{}_format".format(log_format))
        except AttributeError:
            self.format_event = formatEventAsClassicLogText

    def __call__(self, event):
        return self.emit(event)  # pragma nocover

    def emit(self, event):
        if event.get("log_level", LogLevel.info) < self._log_level:
            return
        text = self.format_event(event)

        if self._output:
            self._output.write(unicode(text)+"\n")
            self._output.flush()

    def null_format(self, event):
        return

    def human_format(self, event):
        ev = formatEvent(event)
        return "{:0>7.3f} {:>8} {}".format(
            event['log_time'] - self._start,
            event['log_level'].name.upper(),
            ev)

    def json_format(self, event):
        lev = dict()
        keys = event.keys()
        for key in keys:
            if key in ['format', 'log_source', 'log_factory', 'log_legacy',
                       'log_text', 'log_format',
                       'log_namespace', 'factory', 'log_logger']:
                continue
            if key == 'log_level':
                lev[key] = event[key].name
                continue
            if (key in ['reason', 'message', 'failure'] and
                    not isinstance(event[key], str)):
                lev[key] = repr(event[key])
                continue
            lev[key] = event[key]
        return json.dumps(lev, skipkeys=True)

    def dump(self):
        try:
            self._output.seek(0)
            return self._output.readlines()
        except IOError:
            return []

    def start(self):
        if self._filename:
            self._output = io.open(self._filename, "a", encoding="utf-8")
        # we're already sending to stdout, so no need to duplicate.
        if self._output and self._output != sys.stdout:
            begin_or_register(self)

    def stop(self):
        if self._output and self._output != sys.stdout:
            globalLogPublisher.removeObserver(self)
            if self._filename:
                self._output.close()
                self._output = None
