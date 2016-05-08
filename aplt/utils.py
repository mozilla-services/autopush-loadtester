"""Scenario utilities"""

import string
import random


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
