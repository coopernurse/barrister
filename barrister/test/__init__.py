"""
    barrister
    ~~~~~~~~~

    A RPC toolkit for building lightweight reliable services.  Ideal for
    both static and dynamic languages.

    :copyright: (c) 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""
import unittest

from .runtime_test import RuntimeTest
from .parser_test import ParserTest

def all_tests():
    s = [ ]
    s.append(unittest.TestLoader().loadTestsFromTestCase(ParserTest))
    s.append(unittest.TestLoader().loadTestsFromTestCase(RuntimeTest))
    return unittest.TestSuite(s)
