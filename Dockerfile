# Mozilla AutoPush Load-Tester

# VERSION    0.1

# Extend base debian
FROM stackbrew/debian:sid

MAINTAINER Ben Bangert <bbangert@mozilla.com>

RUN mkdir -p /home/ap-loadtester
ADD . /home/ap-loadtester/

WORKDIR /home/ap-loadtester

RUN \
    apt-get update; \
    apt-get install -y -qq make curl wget bzip2 libexpat1-dev gcc libssl-dev libffi-dev; \
    apt-get install -y -qq python-virtualenv; \
    apt-get install -y -qq libexpat1 libssl1.0.0 libffi6; \
    wget https://bitbucket.org/pypy/pypy/downloads/pypy2-v5.3.1-linux64.tar.bz2; \
    tar xjvf pypy2-v5.3.1-linux64.tar.bz2; \
    /usr/bin/virtualenv -p pypy2-v5.3.1-linux64/bin/pypy apenv; \
    ./apenv/bin/pip install --upgrade pip; \
    ./apenv/bin/pip install -U setuptools; \
    ./apenv/bin/pip install pyasn1; \
    ./apenv/bin/python setup.py develop; \
    apt-get remove -y -qq make curl wget bzip2 libexpat1-dev gcc libssl-dev libffi-dev; \
    apt-get autoremove -y -qq; \
    apt-get clean -y
# End run

CMD ["./apenv/bin/aplt_testplan"]
