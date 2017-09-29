# Scenarios

The basic unit of a test-plan is a scenario, which indicates a set of
instructions that should be run. Many instances of a scenario can be run at once
using `aplt_testplan` to launch them.

If you're interested in using this tool as a simple "smoke-test" system, you only
need to worry about scenarios.

A scenario is a Python generator function, which yields each command it wants
executed. (See [scenarios.py](aplt/scenarios.py) for examples of scenario functions.) 
Any additional logic the scenario wishes to perform can be done with
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
take time and block other scenarios from running. If you need to perform such 
tasks, consider creating [commands](#commands). 

See [scenarios.py](aplt/scenarios.py) for examples of scenario functions.

## Smoke Testing

A "smoke test" is an application which checks that a targeted system continues to operate and intergrate as expected.
These are usually one or more simple, targeted transactions or commands that quickly check for normal behavior.

Some scenarios (e.g. [`basic` in scenarios](aplt/scenarios.py)) could be run as a stand-alone "smoke test". This 
scenario opens a websocket connection, and then sends a known data set via the push endpoint. It waits for the 
system to send the data back over the websocket connection, and checks that the data meets expectations. This does 
require some mock settings to handle expected encryption (which is normally dealt with by the client), however 
the those elements are conceded to be outside of the testing scope. `basic` can be used as a simple, positive 
smoke test that the autopush application continues to operate normally.

To aide in smoke testing, some additional features have been made available. 

### Simplified scenario calling

If you wish to call a scenario that is located in `aplt/scenarios.py`, you can use the function name directly. Also
note that the websocket target is presumed to be the autopush production service link.

e.g. 
```bash
aplt_scenario basic
```

This is equivalent to the longer 

```bash
aplt_scenario aplt.scenarios:basic wss://push.services.mozilla.com/
```

### Configuration files
Common arguments can be stored in `config.ini`. A sample `config.ini.sample` file contains descriptions of 
the arguments, and default values. These values will become default for any subsequent call to either 
`aplt_scenario` or `aplt_testplan`, but can be overridden either by the command line or environment 
variable (see the help returned by the `--help` option.) 

### Log Output
Output logging can be controlled by using each of the logging options:

#### log_level
This option controls the minimum loggable level to record. You can use ('debug', 'info', 'warn', 'error' or 'critical')
as a parameter, and increase in importance from 'debug' to 'critical' Logging defaults to 'info' level. 
Values less than 'warn' may produce more verbose output.

#### log_output
This option controls where logging information will be written. You can use ('stdout', 'none', or a valid, writable 
file path name) The default is 'stdout', which is the Standard Output channel. 'none' prevents any logging information
from being displayed.

#### log_format
This option controls the format of the log message. You can use ('default', 'json' or 'human'). The default is 
'default', and is in standard python logging format. 'json' wraps each output line as a JSON readable entity and
is designed for easy parsing by automated systems. 'human' provides a more 'human' readable error message which may
be easier to scan for information.

## Commands

Commands which send websocket messages to the server or retrieve messages from
the push service will return the Python dict of the raw server response as
documented in [the SimplePush protocol docs](http://mozilla-push-service.readthedocs.org/en/latest/design/#simplepush-protocol).

Any command that lists *arguments* may need to have all arguments supplied.

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
* [expect_notifications](#expect_notifications)
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

**Arguments:** A channel ID and an optional VAPID public key.

*Note:* If a VAPID public key is specifed, the endpoint becomes a "restricted" endpoint. 
Any future call to [send_notification](#send_notification) will require a VAPID header signed with the
corresponding Private Key. 

```python
yield register("ef4e3d8b-9ecb-4de7-a909-56d9acd60a42")

# or 

yield register("ef4e3d8b-9ecb-4de7-a909-56d9acd60a42", 
               "EJwJZq_GN8jJbo1GGpyU70hmP2hbWAUpQFKDBy"
               "KB81yldJ9GTklBM5xqEwuPM7VuQcyiLDhvovth"
               "PIXx-gsQRQ==""")
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
`None` can be used for `data`. If VAPID headers are desired, include a
valid `claims` dict.

**Arguments:** `endpoint_url`, `data`, `ttl`, `claims`(optional)

```python
yield send_notification('BIG_URL', 'SOME_DATA', 60, claims={sub,"mailto:admin@example.com"})
```
*Claims* is a JSON blob containing the following:

`aud` - The owning URL for the subscription; This is the main URL for
the site that publishes the subscription. (e.g. If a user has
subscribed to Push Notifications from "Example.com", the `aud` could
be `https://example.com`) If no value is specified, one will be derived
from the endpoint.

`sub` - The email address of the administrative contact for the
subscription.  (e.g. for the above `aud` the address for the
administrative contact could be `mailto: admin-push@example.com`)

`exp` - The expiration time expressed in UTC seconds for the VAPID
information block. Expired VAPID blocks are considered invalid and
will be rejected.


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

### expect_notifications

Wait on the websocket connection for one of a list of expected notifications to
be delivered. The first notification matching a channel in the list passed will
be returned. `time` is how long to wait before giving up.

**Arguments:** `channel_ids`, `time`

```python
yield expect_notifications([
    "1913165ea4104f1482ee440cedac6abd",
    "57e58ab6ab6f4e5dbb0e8b93304ac844",
    "dc3323f8674948e5ac83e53830e4a8f7"
    ], 5)
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
