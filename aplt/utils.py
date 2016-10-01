"""Scenario utilities"""

import string
import random

from OpenSSL import SSL
from OpenSSL.crypto import FILETYPE_PEM, load_certificate, load_privatekey
from twisted.internet.interfaces import IOpenSSLClientConnectionCreator
from twisted.web.iweb import IPolicyForHTTPS
from zope.interface import implementer


def string_generator(length=10):
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for _ in range(length))


def bad_push_endpoint(push_endpoint=None, token_length=None):
    from random import randint

    """Given a valid endpoint URL, return a new one with an invalid
    token of token_length.

    If token_length not specified, append a random token string of
    random length.

    If no push_endpoint specified, return a bogus endpoint with an
    invalid token.
    """
    if not push_endpoint:
        push_endpoint = '/zoot/allures/cgi-bin/xyz'
    if not token_length:
        token_length = randint(1, 1000)
    parts = push_endpoint.split('/')
    token_bad = string_generator(token_length)
    parts.pop()
    return '/'.join(parts) + '/' + token_bad


@implementer(IPolicyForHTTPS)
class UnverifiedHTTPS(object):
    """An unverified HTTPS policy.

    The remote connection's certificate isn't verified nor is its
    hostname checked.

    Optionally supports sending a client certificate.

    """

    def __init__(self, client_certfile=None, client_keyfile=None):
        if client_keyfile and not client_certfile:
            raise ValueError("client_certfile argument required with "
                             "client_keyfile")

        if client_certfile:
            with open(client_certfile) as fpc:
                self.cert = load_certificate(FILETYPE_PEM, fpc.read())
            if not client_keyfile:
                client_keyfile = client_certfile
            with open(client_keyfile) as fpk:
                self.key = load_privatekey(FILETYPE_PEM, fpk.read())
        else:
            self.cert = self.key = None

    def creatorForNetloc(self, hostname, port):
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.set_options(
            SSL.OP_CIPHER_SERVER_PREFERENCE |
            SSL.OP_NO_SSLv2 |
            SSL.OP_NO_SSLv3 |
            SSL.OP_NO_COMPRESSION |
            SSL.OP_ALL & ~SSL.OP_MICROSOFT_BIG_SSLV3_BUFFER)

        ctx.set_mode(SSL.MODE_RELEASE_BUFFERS)

        if self.cert:
            ctx.use_certificate(self.cert)
            ctx.use_privatekey(self.key)

        return SimpleSSLClientConnectionCreator(ctx)


@implementer(IOpenSSLClientConnectionCreator)
class SimpleSSLClientConnectionCreator(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def clientConnectionForTLS(self, tlsProtocol):
        conn = SSL.Connection(self.ctx, None)
        conn.set_app_data(tlsProtocol)
        return conn
