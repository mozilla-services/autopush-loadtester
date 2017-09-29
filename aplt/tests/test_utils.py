import unittest

from nose.tools import ok_

from aplt.utils import bad_push_endpoint


class Test_Utils(unittest.TestCase):

    def test_bad_push_endpoint(self):
        ep = bad_push_endpoint()
        ok_(ep[:22], '/zoot/allures/cgi-bin/')
        ok_(len(ep) < 1022)
