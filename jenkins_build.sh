#!/bin/sh

set -e

if [ ! -d env ]
then
  virtualenv env
fi
. env/bin/activate
pip install -r requirements.txt
./run_tests.sh

