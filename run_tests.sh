#!/bin/sh

set -e

export PYTHONPATH=`pwd`

# regular unit tests
# use xargs instead of -exec so that we get exit code propegation
find ./barrister/test -name "*_test.py" -print | xargs -n1 python

# conformance test suite
cd conform; rm -f *.out; python conform_test.py
