# Mozilla AutoPush Load-Tester

FROM pypy:2-5.3.1

MAINTAINER Ben Bangert <bbangert@mozilla.com>

RUN mkdir -p /home/ap-loadtester
ADD . /home/ap-loadtester/

WORKDIR /home/ap-loadtester

RUN \
    pip install --upgrade pip && \
    pip install virtualenv && \
    virtualenv -p `which pypy` apenv && \
    ./apenv/bin/pip install pyasn1 && \
    ./apenv/bin/python setup.py develop && \
    apt-get autoremove -y -qq && \
    apt-get clean -y
# End run

CMD ["./apenv/bin/aplt_testplan"]
