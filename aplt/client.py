"""Websocket Client

Handles interactions on behalf of a single client.

"""
import json

from autobahn.twisted.websocket import connectWS, WebSocketClientProtocol


NIL = object()


class MyClientProtocol(WebSocketClientProtocol):
    def onOpen(self):
        self.processor = self.harness.add_client(self)
        self.processor.handle(dict(messageType="connect"))

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


class CommandProcessor(object):
    """Created per Virtual Client to run a client scenario"""
    valid_commands = ["connect", "disconnect", "register", "unregister",
                      "send_notification", "expect_notification", "ack",
                      "wait"]
    valid_handlers = ["connect", "disconnect", "error", "hello",
                      "notification", "register", "unregister"]

    def __init__(self, scenario, factory, context_factory):
        self._factory = factory
        self._context_factory = context_factory
        self._scenario = scenario()

        # Command processing
        self._last_command = None

        # Websocket attributes
        self._connected = False
        self._ws_client = None
        self._notifications = []

    def run(self):
        """Start the scenario"""
        try:
            self._run_command(self._scenario.next())
        except StopIteration:
            return

    def _send_command_result(self, result):
        try:
            self._run_command(self._scenario.send(result))
        except StopIteration:
            return

    def _run_command(self, command):
        command_name = command.__class__.__name__.lower()
        if command_name not in self.valid_commands:
            raise Exception("Invalid command")

        self._last_command = command_name
        self.__dict__[command_name](command)

    def connect(self, command):
        """Run the connect command to start the websocket connection"""
        if self._connected:
            raise Exception("Already connected")
        connectWS(self.factory, self.context_factory)

    def disconnect(self, command):
        """Close the websocket connection"""
        if not self._ws_client:
            raise Exception("Not connected")
        self._ws_client.sendClose()

    def register(self, command):
        """Send the register command to the server"""
        self._send_json(dict(messageType="register",
                             channelID=command.channel_id))

    def unregister(self, command):
        """Send the unregister command to the server"""
        self._send_json(dict(messageType="unregister",
                             channelID=command.channel_id))

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

        if message_type == "notification":
            # Notifications are stored for expect notification calls
            return self._notifications.append(data)

        if self._last_command != message_type:
            # All websocket events except the notification need the command
            # preceding them, or we should cancel the client.
            self._raise_unexpected_event(data)

        if "connect" in message_type:
            # If this is a connect/disconnect, set the connected appropriately
            self._connected = message_type == "connect"

        # Otherwise pass on the result as is to the scenario
        self._send_command_result(data)
