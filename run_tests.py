#!/usr/bin/env python
import sys, os
import unittest
from subprocess import Popen

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from barrister.test import all_tests

unittest.TextTestRunner(verbosity=2).run(all_tests())

python_bin = "python"
env = {"PYTHONPATH":"..", "CONFORM_VERBOSE": "1"}

if os.environ.has_key("VIRTUAL_ENV"):
    venv = os.environ["VIRTUAL_ENV"]
    python_bin = "%s/bin/python" % venv
    env["VIRTUAL_ENV"] = venv
    env["PATH"] = "%s/bin" % venv

print python_bin

p = Popen([python_bin, "conform_test.py"], env=env, cwd="conform")
ret = p.wait()
if ret != 0:
    print "Conformance tests failed"
    sys.exit(1)
