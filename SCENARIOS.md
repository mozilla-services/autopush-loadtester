# Scenarios

The basic unit of a test-plan is a scenario, which indicates a set of
instructions that should be run. Many instances of a scenario can be run at once
using `aplt_testplan` to launch them.

A scenario is a Python generator function, which yields each command it wants
executed. Any additional logic the scenario wishes to perform can be done with
normal Python code. All commands are tuples, some of which return responses as
documented below.

A scenario can also yield generators so that a scenario may be broken into
multiple functions for re-use.

Responses from a command can be assigned to a variable:

```python
reg = yield register(random_channel_id())
```

The response of a command can be ignored by not assigning it to a variable.

```python
yield connect()
```

Scenarios may loop forever in the event that they wish to never terminate.

**Do not call long-running functions in a scenario**, such as writing/reading
a file or making network calls. Interacting with the filesystem or network can
take time and block other scenarios from running.

See [scenarios.py](aplt/scenarios.py) for examples of scenario functions.

## Commands

Commands which send websocket messages to the server or retrieve messages from
the push service will return the Python dict of the raw server response as
documented in [the SimplePush protocol docs](http://mozilla-push-service.readthedocs.org/en/latest/design/#simplepush-protocol).

Any command that lists *arguments* must have all arguments supplied.

Commands *may throw exceptions* if an error occurs. These can occur during any
of the commands should the connection be dropped unexpectedly, or should a
notification fail to send. Exceptions will be thrown where the command was
yielded, and any client connections should be considered invalid.

Full list of commands available in `aplt.commands` module:

* [spawn](#spawn)
* [connect](#connect)
* [disconnect](#disconnect)
* [hello](#hello)
* [register](#register)
* [unregister](#unregister)
* [send_notification](#send_notification)
* [expect_notification](#expect_notification)
* [ack](#ack)
* [wait](#wait)
* [timer_start](#timer_start)
* [timer_end](#timer_end)
* [counter](#counter)

Additional useful Python functions in `aplt.commands` module (these do not need
a `yield`):

* [random_channel_id](#random_channel_id)
* [random_data](#random_data)


### spawn

Spawns a scenario using a new LoadRunner. The ``test_plan`` should be provided
in the same format as ``aplt_testplan`` accepts.

**Arguments:** `test_plan`

```python
yield spawn("aplt.scenarios:reconnect_forever, 1, 1, 0, 200")
```

**Returns:** ``None``

### connect

Connects the client to the push server.

```python
yield connect()
```

**Returns:**

```python
{"messageType": "connect"}
```

### disconnect

Disconnects the client from the push server.

Note that unclean disconnects are common as many servers drop the connection
immediately.

```python
yield disconnect()
```

**Returns:**

```python
{
    "messageType": "disconnect",
    "was_clean": False,
    "code": 1006,
    "reason": "connection was closed uncleanly (server did not drop TCP connection (in time))"
}
```

### hello

Sends a hello message to the server.

**Arguments:** `None` or a user-agent ID (UAID) to use in the hello message. If
               `None` is used, the server will assign a new UAID.

```python
yield hello(None)
# or
yield hello("f807ecd7-1bd8-4b62-8027-120f18531b01")
```

**Returns:**

```python
{
    "status": 200,
    "messageType": "hello",
    "ping": 60.0,
    "uaid": "f807ecd7-1bd8-4b62-8027-120f18531b01",
    "use_webpush": True
}
```

### register

Register a channel with the push server.

**Arguments:** A channel ID.

```python
yield register("ef4e3d8b-9ecb-4de7-a909-56d9acd60a42")
```

**Returns:**

```python
{
    'status': 200,
    'messageType': 'register',
    'channelID': 'ef4e3d8b-9ecb-4de7-a909-56d9acd60a42',
    'pushEndpoint': 'BIG_URL'
}
```

### unregister

Remove a channel from the push server.

**Arguments:** A channel ID.

```python
yield unregister("ad6a1337-748a-437b-9957-6895f24796a9")
```

**Returns:**

```python
{
    'messageType': 'unregister',
    'status': 200,
    'channelID': 'ad6a1337-748a-437b-9957-6895f24796a9',
}
```

### send_notification

Send a notification to the push service. If an empty data payload is desired,
`None` can be used for `data`.

**Arguments:** `endpoint_url`, `data`, `ttl`

```python
yield send_notification('BIG_URL', 'SOME_DATA', 60)
```

**Returns:** A tuple of (`response`, `content`) corresponding to the result of
             the notification web request. `response` is a [treq response object](http://treq.readthedocs.org/en/latest/api.html#treq.response.Response)
             object, with `content` being the response body content.

### expect_notification

Wait on the websocket connection for an expected notification to be delivered.
`time` is how long to wait before giving up.

**Arguments:** `channel_id`, `time`

```python
yield expect_notification("1913165ea4104f1482ee440cedac6abd", 5)
```

**Returns:** `None` if the timeout was hit, or the following if the expected
             notification arrived.

```python
{
    'messageType': 'notification',
    'version': 'LONG_VERSION_STRING',
    'channelID': 'ad6a1337-748a-437b-9957-6895f24796a9'
}
```

### ack

Acknowledge a notification. The push server may not deliver further
notifications until sent ones are acknowledged.

**Arguments:** `channel_id`, `version`

```python
yield ack("ad6a1337-748a-437b-9957-6895f24796a9", "LONG_VERSION_STRING")
```

**Returns:** `None`

### wait

Waits a `time` seconds before proceeding.

**Arguments:** `time`

```python
yield time(10)
```

**Returns:** `None`

### timer_start

Starts a metric timer of the given `name`. An exception will be thrown if a
timer of this name was already started.

**Arguments:** `name`

```python
yield timer_start("update.latency")
```

**Returns:** `None`

### timer_end

Ends a metric timer of the given `name`. An exception will be thrown if a timer
of this name was not already started.

**Arguments:** `name`

```python
yield timer_end("update.latency")
```

**Returns:** `None`

### counter

Send a counter of the given `name` with the given `count`.

**Arguments:** `name`, `count`

```python
yield counter("notification.sent", 1)
```

### random_channel_id

Generate and return a random UUID appropriate for a UAID or channel id.

```python
channel_id = random_channel_id()
```

### random_data

Generate and return random binary data between the given min/max data length.

```python
data = random_data(2048, 4096)
```

## Decorators

Scenario decorators modify the behavior of a scenario.

Full list of commands available in `aplt.decorators` module:

* [restart](#restart)

### restart

Restart the scenario in the event an uncaught exception occurs. Takes one
parameter indicating how many times the scenario should be restarted if an
error occurs, ``0`` may be used to indicate indefinite retries.

```python
@restart(2)
def my_scenario():
    ...
```
