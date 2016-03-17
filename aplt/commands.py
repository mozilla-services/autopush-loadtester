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


class register(namedtuple("Register", "channel_id")):
    pass


class unregister(namedtuple("UnRegister", "channel_id")):
    pass


class send_notification(namedtuple("SendNotification",
                                   "endpoint_url data ttl")):
    pass


class expect_notification(namedtuple("ExpectNotification", "channel_id time")):
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
