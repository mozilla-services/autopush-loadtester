"""Commands to run per tester"""
import uuid
from collections import namedtuple


# Command types are basic named tuples to encapsulate possible arguments and
# enforce argument checking
# Note that these are all class declarations for consistency even though some
# of them don't need defaults
class connect(namedtuple("Connect", "")):
    pass


class disconnect(namedtuple("Disconnect", "")):
    pass


class hello(namedtuple("Hello", "uaid")):
    def __init__(self, uaid=None):
        self.uaid = uaid


class register(namedtuple("Register", "channel_id")):
    def __init__(self, channel_id=None):
        self.channel_id = channel_id or random_channel_id()


class unregister(namedtuple("UnRegister", "channel_id")):
    def __init__(self, channel_id=None):
        self.channel_id = channel_id


class send_notification(namedtuple("SendNotification", "channel_id data")):
    pass


class expect_notification(namedtuple("ExpectNotification", "channel_id")):
    pass


class ack(namedtuple("Ack", "message_id")):
    pass


class wait(namedtuple("Wait", "time")):
    pass


# Helper functions to use with commands
def random_channel_id():
    return uuid.uuid4().hex
