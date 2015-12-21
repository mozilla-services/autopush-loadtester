"""Websocket Client

Handles interactions on behalf of a single client.

"""
import json

from autobahn.twisted.websocket import WebSocketClientProtocol
from twisted.protocols import policies
from twisted.python import log


class WSClientProtocol(WebSocketClientProtocol):
    def onOpen(self):
        self.processor = self.harness.add_client(self)
        self.processor.handle(dict(messageType="connect", client=self))

    def onMessage(self, payload, isBinary):
        try:
            data = json.loads(payload)
        except Exception as exc:
            self.processor.handle(dict(messageType="error", exception=exc))
        else:
            self.processor.handle(data)

    def onClose(self, wasClean, code, reason):
        self.harness.remove_client(self)

        try:
            self.processor.handle(dict(messageType="disconnect",
                                       was_clean=wasClean, code=code,
                                       reason=reason))
        except AttributeError:
            pass


class CommandProcessor(object, policies.TimeoutMixin):
    """Created per Virtual Client to run a client scenario"""
    valid_commands = ["connect", "disconnect", "register", "hello",
                      "unregister", "send_notification", "expect_notification",
                      "ack", "wait"]
    valid_handlers = ["connect", "disconnect", "error", "hello",
                      "notification", "register", "unregister"]

    def __init__(self, scenario, harness):
        self._harness = harness
        self._scenario = scenario()

        # Command processing
        self._last_command = None
        self._expecting = None
        self._waiting = False

        # Websocket attributes
        self._connected = False
        self._ws_client = None
        self._notifications = []

    def run(self):
        """Start the scenario"""
        self._run_safely(lambda: self._scenario.next())

    def _send_command_result(self, result):
        self._run_safely(lambda: self._scenario.send(result))

    def _run_safely(self, func, throw=False):
        try:
            self._run_command(func())
        except StopIteration:
            self._harness.remove_processor()
        except:
            log.err()
            self._harness.remove_processor()

    def _run_command(self, command):
        log.msg("Running command: ", command)
        command_name = command.__class__.__name__
        try:
            if command_name not in self.valid_commands:
                raise Exception("Invalid command: %s" % command_name)

            self._last_command = command_name
            getattr(self, command_name)(command)
        except:
            # Log the exception and shutdown the client
            log.err()
            self._harness.remove_processor()

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
        # already
        if self._expecting:
            return

        # Notification not found, set a timeout waiting for it
        self._expecting = command
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

    def timeoutConnection(self):
        """Called by the timer when a timeout has hit"""
        if self._expecting:
            self._send_command_result(None)

        if self._waiting:
            self._waiting = False
            self._send_command_result(None)
        self.setTimeout(None)

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
                self.expect_notification(self._expecting)
            return

        if self._last_command != message_type:
            # All websocket events except the notification need the command
            # preceding them, or we should cancel the client.
            self._raise_unexpected_event(data)

        if "connect" in message_type:
            # If this is a connect/disconnect, set the connected appropriately
            self._connected = message_type == "connect"
            self._ws_client = data.pop("client", None)

        # Otherwise pass on the result as is to the scenario
        self._send_command_result(data)
