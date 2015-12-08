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
)


def basic():
    yield connect()
    yield hello(None)
    reg = yield register(random_channel_id())
    response, content = yield send_notification(reg["pushEndpoint"], None, 60)
    notif = yield expect_notification(reg["channelID"], 5)
    log.msg("Got notif: ", notif)
    yield ack(channel_id=notif["channelID"], version=notif["version"])
    yield unregister(reg["channelID"])
    yield disconnect()
