#!/bin/sh

set -e

if [ ! -d env ]
then
  virtualenv env
fi
. env/bin/activate
./env/bin/pip install -r requirements.txt
./run_tests.sh

if [ -n "$BARRISTER_NODE" ]
then
  npm install $BARRISTER_NODE
fi

# generate docs
rm -rf doc
epydoc -q --parse-only -o doc --docformat=restructuredText --exclude=test barrister
