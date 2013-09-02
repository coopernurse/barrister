#!/bin/sh

set -e

export GH=/home/james/github
export BARRISTER=$GH/barrister
export BARRISTER_JAVA=$GH/barrister-java
export BARRISTER_NODE=$GH/barrister-js
export BARRISTER_RUBY=$GH/barrister-ruby
export BARRISTER_PHP=$GH/barrister-php
export CONFORM_VERBOSE=1
export GOPATH=/home/james/go
export JAVA_HOME=/usr/local/java
export PATH=$PATH:$GOROOT/bin:$JAVA_HOME/bin:/usr/local/maven/bin
export NODE_PATH=$NODE_PATH:$BARRISTER/node_modules

git pull
./jenkins_build.sh
rsync -avz doc/ james@barrister.bitmechanic.com:/home/james/barrister-site/api/python/latest/
