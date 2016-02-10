"""Several basic push scenarios"""
from twisted.python import log

from aplt.commands import (
    connect,
    hello,
    register,
    send_notification,
    expect_notification,
    unregister,
    disconnect,
    ack,
    random_channel_id,
    random_data,
    timer_start,
    timer_end,
    counter,
    wait,
    spawn,
)
from aplt.decorators import restart


def basic():
    """Connects, sends a notification, than disconnects"""
    yield connect()
    yield hello(None)
    reg = yield register(random_channel_id())
    yield timer_start("update.latency")
    response, content = yield send_notification(reg["pushEndpoint"], None, 60)
    yield counter("notification.sent", 1)
    notif = yield expect_notification(reg["channelID"], 5)
    yield counter("notification.received", 1)
    yield timer_end("update.latency")
    log.msg("Got notif: ", notif)
    yield ack(channel_id=notif["channelID"], version=notif["version"])
    yield counter("notification.ack", 1)
    yield unregister(reg["channelID"])
    yield disconnect()


def basic_forever(notif_delay=300, run_once=0):
    yield connect()
    yield hello(None)
    reg = yield register(random_channel_id())

    while True:
        length, data = random_data(min_length=2048, max_length=4096)
        yield timer_start("update.latency")
        response, content = yield send_notification(reg["pushEndpoint"], data,
                                                    60)
        yield counter("notification.throughput.bytes", length)
        yield counter("notification.sent", 1)
        notif = yield expect_notification(reg["channelID"], 5)
        yield counter("notification.sent", 1)
        yield timer_end("update.latency")
        yield ack(channel_id=notif["channelID"], version=notif["version"])
        yield counter("notification.ack", 1)
        yield wait(notif_delay)
        if run_once:
            yield disconnect()
            break


def connect_and_idle_forever():
    yield connect()
    yield hello(None)

    while True:
        yield wait(100)


def reconnect_forever(reconnect_delay=300, run_once=0):
    """Reconnects every delay interval, sends a notification

    Repeats forever.

    """
    yield connect()
    response = yield hello(None)
    reg = yield register(random_channel_id())
    assert "uaid" in response
    uaid = response["uaid"]

    while True:
        length, data = random_data(min_length=2048, max_length=4096)
        yield timer_start("update.latency")
        response, content = yield send_notification(reg["pushEndpoint"], data,
                                                    60)
        yield counter("notification.throughput.bytes", length)
        yield counter("notification.sent", 1)
        notif = yield expect_notification(reg["channelID"], 5)
        yield counter("notification.received", 1)
        yield ack(channel_id=notif["channelID"], version=notif["version"])
        yield counter("notification.ack", 1)
        yield timer_end("update.latency")
        yield wait(reconnect_delay)
        yield disconnect()
        yield connect()
        response = yield hello(uaid)
        assert response["uaid"] == uaid

        if run_once:
            yield disconnect()
            break


##############################################################################
# TEST SCENARIOS
##############################################################################
_RESTARTS = 0


@restart(2)
def _explode():
    global _RESTARTS
    yield connect()
    _RESTARTS += 1
    yield connect()


def _test_spawn():
    yield spawn("aplt.scenarios:basic, 1, 1, 0")
