# Autopush Load-Tester

The Autopush Load-Tester is an integrated tester and load-tester for the Mozilla
Services autopush project. It's intented to verify proper functioning of
autopush deployments under various load conditions.

## Developing

`ap-loadtester` uses PyPy 4.0.1 which can be downloaded here:
http://pypy.org/download.html

You will also need virtualenv installed on your system to setup a virtualenv for
`ap-loadtester`. Assuming you have virtualenv and have downloaded pypy, you
could then setup the loadtester for use with the following commands:

    $ tar xjvf pypy-4.0.1-linux64.tar.bz2
    $ virtualenv -p pypy-4.0.1-linux64/bin/pypy apenv
    $ source apenv/bin/activate
    $ pip install --upgrade pip

The last two commands activate the virtualenv so that running python or pip on
the shell will run the virtualenv pypy, and upgrade the installed pip to the
latest version.

Now install the requirements for `ap-loadtester`, and run the package setup for
the command line script to be ready:

    $ pip install -r requirements.txt
    $ python setup.py --develop
