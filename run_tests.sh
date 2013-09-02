#!/bin/sh

set -e

export PYTHONPATH=`pwd`

# regular unit tests
# use xargs instead of -exec so that we get exit code propegation
find ./barrister/test -name "*_test.py" -print | xargs -n1 python

# run script to test parsing various IDL files
./idl_parse_test.sh

# build barrister-go bits
cd $GOPATH/src/github.com/coopernurse/barrister-go/conform
rm -rf generated
go run ../idl2go/idl2go.go -n -b "github.com/coopernurse/barrister-go/conform/generated/" -d generated $PYTHONPATH/conform/conform.json
go build client.go
go build server.go
cd -

# conformance test suite
cd conform; rm -f *.out; python conform_test.py
