#!/bin/sh

set -e

export GH=/usr/local/github
export BARRISTER=$GH/barrister
export BARRISTER_JAVA=$GH/barrister-java
export BARRISTER_NODE=$GH/barrister-js
export BARRISTER_RUBY=$GH/barrister-ruby
export BARRISTER_PHP=$GH/barrister-php
export CONFORM_VERBOSE=1
export GOROOT=/usr/local/go
export GOPATH=$HOME/go
export PATH=$PATH:$GOROOT/bin
export NODE_PATH=$NODE_PATH:$BARRISTER/node_modules

ln -s $BARRISTER_NODE $BARRISTER_NODE/node_modules/barrister

git pull
./jenkins_build.sh
#rsync -avz doc/ james@barrister.bitmechanic.com:/home/james/barrister-site/api/python/latest/
