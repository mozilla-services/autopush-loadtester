"""Websocket Client

Handles interactions on behalf of a single client.

"""
import json
import time
import types
import sys

from autobahn.twisted.websocket import WebSocketClientProtocol
from twisted.internet import reactor
from twisted.protocols import policies
from twisted.python import log


class WSClientProtocol(WebSocketClientProtocol):
    def onOpen(self):
        self.processor = self.factory.harness.add_client(self)
        if not self.processor:
            # Unnecessary open, no one waiting
            return
        self.processor.handle(dict(messageType="connect", client=self))

    def onMessage(self, payload, isBinary):
        try:
            data = json.loads(payload)
        except Exception as exc:
            self.processor.handle(dict(messageType="error", exception=exc))
        else:
            self.processor.handle(data)

    def onClose(self, wasClean, code, reason):
        self.factory.harness.remove_client(self)

        try:
            self.processor.handle(dict(messageType="disconnect",
                                       was_clean=wasClean, code=code,
                                       reason=reason))
        except AttributeError:
            pass


class CommandProcessor(object, policies.TimeoutMixin):
    """Created per Virtual Client to run a client scenario"""
    valid_commands = ["spawn", "connect", "disconnect", "register", "hello",
                      "unregister", "send_notification", "expect_notification",
                      "expect_notifications", "ack", "wait", "timer_start",
                      "timer_end", "counter"]
    valid_handlers = ["connect", "disconnect", "error", "hello",
                      "notification", "register", "unregister"]

    def __init__(self, scenario, scenario_args, harness):
        self._harness = harness
        self._retries = getattr(scenario, "_retries", None)
        self._current_tries = 0
        self._scenario_func = scenario
        self._scenario_args = scenario_args

        self._reset()

    def _reset(self):
        """Reset for a startover or initialization"""
        # Setup the scenario
        self._scenario = [self._scenario_func(*self._scenario_args)]

        # Command processing
        self._last_command = None
        self._expecting = None
        self._waiting = False

        # Websocket attributes
        self._connected = False
        self._ws_client = None
        self._notifications = []
        self._timers = {}

        # Ensure no timers are set
        self.setTimeout(None)

    def run(self):
        """Start the scenario"""
        self._run_safely(lambda: self._scenario[-1].next())

    def shutdown(self, ended):
        """Shutdown the scenario after it's over, if needed"""
        self._current_tries += 1
        retry = self._retries == 0 or (self._current_tries <= self._retries)
        if ended or (not retry):
            self._harness.remove_processor()
        else:
            # Start it back up again!
            self._reset()
            self.run()

    def _send_command_result(self, result):
        self._run_safely(lambda: self._scenario[-1].send(result))

    def _send_exception(self):
        """Send the current exception being handled into a generator and drop
        any active connection"""
        if self._connected:
            self._connected = False
            # Remove ourselves as a processor so we don't get the closed event
            del self._ws_client.processor

            # Send the close, and drop our reference to the client
            self._ws_client.sendClose()
            self._ws_client = None

        def throw():
            self._scenario[-1].throw(*sys.exc_info())
        self._run_safely(throw)

    def _run_safely(self, func, throw=False):
        try:
            self._run_command(func())
        except StopIteration:
            if len(self._scenario) == 1:
                self.shutdown(ended=True)
            else:
                self._scenario.pop()
                reactor.callLater(0, self._send_command_result, None)
        except:
            log.err()
            self.shutdown(ended=False)

    def _run_command(self, command):
        if isinstance(command, types.GeneratorType):
            self._scenario.append(command)
            reactor.callLater(0, self.run)
            return
        log.msg("Running command: ", command)
        command_name = command.__class__.__name__
        if command_name not in self.valid_commands:
            raise Exception("Invalid command: %s" % command_name)

        self._last_command = command_name
        command_func = getattr(self, command_name)

        try:
            command_func(command)
        except:
            self._send_exception()

    def spawn(self, command):
        """Spawn a new test plan"""
        self._harness.spawn(command.test_plan)
        self._send_command_result(None)

    def connect(self, command):
        """Run the connect command to start the websocket connection"""
        if self._connected:
            raise Exception("Already connected")
        self._harness.connect(self)

    def disconnect(self, command):
        """Close the websocket connection"""
        if not self._ws_client:
            raise Exception("Not connected")
        self._ws_client.sendClose()

    def hello(self, command):
        cmd = dict(messageType="hello", use_webpush=True)
        if command.uaid:
            cmd["uaid"] = command.uaid
        self._send_json(cmd)

    def register(self, command):
        """Send the register command to the server"""
        self._send_json(dict(messageType="register",
                             channelID=command.channel_id))

    def unregister(self, command):
        """Send the unregister command to the server"""
        self._send_json(dict(messageType="unregister",
                             channelID=command.channel_id))

    def send_notification(self, command):
        """Send a notification to the given endpoint URL"""
        self._harness.send_notification(self, url=command.endpoint_url,
                                        data=command.data,
                                        ttl=command.ttl)

    def expect_notification(self, command):
        """Expect a notification to arrive, if its already arrived then act
        on that"""
        notifs = filter(lambda x: x["channelID"] == command.channel_id,
                        self._notifications)
        if notifs:
            notif = notifs[0]
            self._notifications.remove(notif)
            self._expecting = None
            self.setTimeout(None)
            return self._send_command_result(notif)

        # If we're already expecting a notification, the timeout is set
        # already. This can occur when we've called for an incoming client
        # message vs. a command run from a yield.
        if self._expecting:
            return

        # Notification not found, set a timeout waiting for it
        self._expecting = lambda: self.expect_notification(command)
        self.setTimeout(command.time)

    def expect_notifications(self, command):
        """Expect one of many notifications, if one has already arrived that
        is in the set then act on that"""
        if self._notifications:
            for idx, notif in enumerate(self._notifications):
                if notif["channelID"] in command.channel_ids:
                    self._notifications.pop(idx)
                    self._expecting = None
                    self.setTimeout(None)
                    return self._send_command_result(notif)

        if self._expecting:
            return

        self._expecting = lambda: self.expect_notifications(command)
        self.setTimeout(command.time)

    def wait(self, command):
        """Wait for a period of time"""
        self._waiting = True
        self.setTimeout(command.time)

    def ack(self, command):
        """Acknowledge a message id"""
        self._send_json(dict(
            messageType="ack",
            updates=[dict(channelID=command.channel_id,
                          version=command.version)]
        ))
        # We don't get a result of confirmation of ack's
        self._send_command_result(None)

    def timer_start(self, command):
        """Start a metric timer"""
        if command.name in self._timers:
            raise Exception("Can't start a timer that was already started: %s"
                            % command.name)

        self._timers[command.name] = time.time()
        self._send_command_result(None)

    def timer_end(self, command):
        """End a metric timer, handle its submission"""
        start = self._timers.pop(command.name, None)
        if not start:
            raise Exception("Can't end a timer that wasn't started: %s" %
                            command.name)
        duration = int((time.time() - start) * 1000)
        self._harness.timer(command.name, duration)
        self._send_command_result(duration)

    def counter(self, command):
        """Metric Counter"""
        self._harness.counter(command.name, command.count)
        self._send_command_result(None)

    def timeoutConnection(self):
        """Called by the timer when a timeout has hit"""
        self.setTimeout(None)
        if self._expecting:
            self._expecting = None
            self._send_command_result(None)

        if self._waiting:
            self._waiting = False
            self._send_command_result(None)

    def _send_json(self, data):
        if not self._ws_client:
            raise Exception("Not connected")
        self._ws_client.sendMessage(json.dumps(data).encode('utf8'), False)

    def _raise_unexpected_event(self, data):
        """Helper for raising an error when an unexpected event is handled"""
        raise Exception("Unexpected event. Last Command: %s; Data: %s" % (
                        self._last_command, data))

    def handle(self, data):
        """Handles data coming in from the websocket client"""
        message_type = data.get("messageType")
        if message_type not in self.valid_handlers:
            raise Exception("Unexpected data payload: %s", data)

        log.msg("Handling websocket data: ", data)

        if message_type == "notification":
            # Notifications are stored for expect notification calls
            self._notifications.append(data)
            # If we are expecting, trigger it to check
            if self._expecting:
                self._expecting()
            return

        if self._last_command != message_type:
            # All websocket events except the notification need the command
            # preceding them. Otherwise we throw an exception into the
            # scenario.
            try:
                self._raise_unexpected_event(data)
            except:
                self._send_exception()

        if "connect" in message_type:
            # If this is a connect/disconnect, set the connected appropriately
            self._connected = message_type == "connect"
            self._ws_client = data.pop("client", None)

        # Otherwise pass on the result as is to the scenario
        self._send_command_result(data)
