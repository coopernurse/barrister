#!/usr/bin/env python

import sys
import barrister

trans    = barrister.HttpTransport("http://localhost:9233/")
client   = barrister.Client(trans, validate_request=False)

num = int(sys.argv[1])

s = "safasdfasdlfasjdflkasjdflaskjdflaskdjflasdjflaskdfjalsdkfjasldkfjasldkasdlkasjfasld"

for i in range(num):
    client.B.echo(s)
