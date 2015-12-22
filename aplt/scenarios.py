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
    timer_start,
    timer_end,
    counter,
)


def basic():
    yield connect()
    yield hello(None)
    reg = yield register(random_channel_id())
    yield timer_start("notif_send")
    response, content = yield send_notification(reg["pushEndpoint"], None, 60)
    notif = yield expect_notification(reg["channelID"], 5)
    yield timer_end("notif_send")
    yield counter("notif_Sent", 1)
    log.msg("Got notif: ", notif)
    yield ack(channel_id=notif["channelID"], version=notif["version"])
    yield unregister(reg["channelID"])
    yield disconnect()
