import unittest

from .runtime_test import RuntimeTest
from .parser_test import ParserTest

def all_tests():
    s = [ ]
    s.append(unittest.TestLoader().loadTestsFromTestCase(ParserTest))
    s.append(unittest.TestLoader().loadTestsFromTestCase(RuntimeTest))
    return unittest.TestSuite(s)
