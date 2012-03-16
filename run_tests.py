#!/usr/bin/env python
import sys, os
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from barrister.test import all_tests

unittest.TextTestRunner(verbosity=2).run(all_tests())
