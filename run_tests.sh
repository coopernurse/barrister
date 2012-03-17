#!/bin/sh

set -e

export PYTHONPATH=`pwd`

# regular unit tests
find ./barrister/test -name "*_test.py" -exec python {} \; -print

# conformance test suite
cd conform; python conform_test.py
