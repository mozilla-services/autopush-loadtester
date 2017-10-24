# Using ap-loadtester as a Smoke Test system

`ap-loadtester` provides a fairly comprehensive set of funcitons and
scripts which are well suited to exercise much of [`autopush`](https://github.com/mozilla-services/autopush). It makes
some sense to use that same rich environment to run simple smoketests
to esure that basic functions are being performed.

## Calling

The simplest approach is to use a a simple command line to start the
exercise.

For example:
``` shell
bin/aplt_scenario --log_format=human basic \
 wss://push.services.mozilla.com/ \
 vapid_claims='{"sub":"mailto:foo@example.com"}'
```

This will run the `basic` function from `aplt/scenarios.py`, targeting
`wss://push.services.mozilla.com/` with `log_format` set to `human`
readable and use the provided VAPID claims dict. (`exp` and `aud` will
be automatically inserted into the VAPID claims.)

`basic` will:
 * create a new subscription locked to a VAPID endpoint
 * send a test message to that subscription endpoint using VAPID auth
 * verify that the message was received
 * confirm the message back to the server
 * clean up the channel information and disconnect

This is a full exercise of the key message exchange elements. The
`basic` function is reasonably well documented, and can be easily
extended or replaced with an even more comprehensive test.


## Configuration
If you find that you use a number of common arguments, you can
place these in a `config.ini` file. See the `config.ini.sample` for
a description of the options and possible values. Uncomment a value by
removing the leading `#` to make that option active.

You can run `bin/aplt_scenario -c <config file name>` to specify the
specific configuration file to run.

e.g.
``` shell
bin/aplt_scenario -c alt_config.ini
```

will run `aplt_scenario` using the configuration file `alt_config.ini`

## Getting help
As always, help is available by calling

``` shell
bin/aplt_scenario --help
```
