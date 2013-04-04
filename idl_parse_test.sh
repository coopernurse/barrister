#!/bin/bash

# files that should parse
okIdl=("project2.idl" "ok-service.idl")

# files that should not parse
badIdl=("project-with-ns.idl" "broken1.idl" "invalid-service.idl" "bad-circle.idl")

for item in ${okIdl[*]}
do
	barrister "barrister/test/idl/$item" > /dev/null
	if [ "$?" -ne "0" ] 
	then
		echo "IDL parse failed: $item"
		exit 1
	fi
done


for item in ${badIdl[*]}
do
	barrister "barrister/test/idl/$item" > /dev/null 2>&1
	if [ "$?" -eq "0" ] 
	then
		echo "Invalid IDL parse worked: $item"
		exit 1
	fi
done
