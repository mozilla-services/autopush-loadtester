"""Commands to run per tester"""
import os
import random
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
    pass


class register(namedtuple("Register", "channel_id key")):
    pass


# set defaults so that we can have the key be optional.
register.__new__.__defaults__ = (None, None)


class unregister(namedtuple("UnRegister", "channel_id")):
    pass


class send_notification(namedtuple("SendNotification",
                                   "endpoint_url data headers claims")):
    pass


# set defaults so that we can have the claims be optional.
send_notification.__new__.__defaults__ = (None, None, None, None)


class expect_notification(namedtuple("ExpectNotification", "channel_id time")):
    pass


class expect_notifications(namedtuple("ExpectNotifications",
                                      "channel_ids time")):
    pass


class ack(namedtuple("Ack", "channel_id version")):
    pass


class wait(namedtuple("Wait", "time")):
    pass


class timer_start(namedtuple("TimerStart", "name")):
    pass


class timer_end(namedtuple("TimerEnd", "name")):
    pass


class counter(namedtuple("Counter", "name count")):
    pass


class spawn(namedtuple("Spawn", "test_plan")):
    pass


# Helper functions to use with commands
def random_channel_id():
    return str(uuid.uuid4())


def random_data(min_length, max_length=4096):
    if min_length == max_length:
        length = min_length
    else:
        length = random.randrange(min_length, max_length)
    return length, os.urandom(length)
