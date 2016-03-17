[![codecov.io](https://codecov.io/github/mozilla-services/ap-loadtester/coverage.svg?branch=master)](https://codecov.io/github/mozilla-services/ap-loadtester?branch=master) [![Build Status](https://travis-ci.org/mozilla-services/ap-loadtester.svg?branch=feature%2Fbug-1)](https://travis-ci.org/mozilla-services/ap-loadtester)

# Autopush Load-Tester

The Autopush Load-Tester is an integrated tester and load-tester for the Mozilla
Services autopush project. It's intented to verify proper functioning of
autopush deployments under various load conditions.

## Getting Started

`ap-loadtester` uses PyPy 5.0 which can be downloaded here:
http://pypy.org/download.html

You will also need virtualenv installed on your system to setup a virtualenv for
`ap-loadtester`. Assuming you have virtualenv and have downloaded pypy, you
could then setup the loadtester for use with the following commands:

**Linux:**

    $ tar xjvf pypy-5.0.0-linux64.tar.bz2
    $ virtualenv -p pypy-5.0.0-linux64/bin/pypy apenv

**OSX:**

    $ tar xjvf pypy-5.0.0-osx64.tar.bz2
    $ virtualenv -p pypy-5.0.0-osx64/bin/pypy apenv

**Activate Virtualenv:**

    $ source apenv/bin/activate
    $ pip install --upgrade pip

The last two commands activate the virtualenv so that running python or pip on
the shell will run the virtualenv pypy, and upgrade the installed pip to the
latest version.

You can now either install `ap-loadtester` as a [program](#program-use) to run
test scenarios you create, or if adding scenarios/code to `ap-loadtester`
continue to [Developing](#developing).


## Program Use

Install the `ap-loadtester` package:

    $ easy_install install ap-loadtester

Run the basic scenario against the dev server:

    $ aplt_scenario wss://autopush-dev.stage.mozaws.net/ aplt.scenarios:basic

Run 5 instances of the basic scenario, starting one every second, against the
dev server:

    $ aplt_testplan wss://autopush-dev.stage.mozaws.net/ "aplt.scenarios:basic 5 1 0"

Either of these scripts can be run with `-h` for full help documentation.

See [SCENARIOS](SCENARIOS.md) for guidance on writing a scenario function for
use with `ap-loadtester`.

## Developing

Checkout the code from this repository and run the package setup after the
virtualenv is active:

    $ python setup.py develop

See [Contributing](CONTRIBUTING.md) for contribution guidelines.

## Notes on Installation

**'openssl/aes.h' file not found**

If you get the following error:

    $ fatal error: 'openssl/aes.h' file not found

Linux: You'll need to install OpenSSL:

    $ sudo apt-get install libssl-dev

OSX: Apple has deprecated OpenSSL in favor of its own TLS and crypto libraries.
If you get this error on OSX (El Capitan), install OpenSSL with brew, then
link brew libraries and install cryptography:

    $ brew install openssl
    $ env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" pip install cryptography


**missing required distribution pyasn1**

If you get the following error:

    $ error: Could not find required distribution pyasn1

re-run:

    $ python setup.py develop
