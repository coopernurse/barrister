#!/usr/bin/env python

import sys
import barrister
import codecs
try:
    import json
except:
    import simplejson as json

trans    = barrister.HttpTransport("http://localhost:9233/")
client   = barrister.Client(trans, validate_request=False)

f   = open(sys.argv[1])
out = codecs.open(sys.argv[2], "w", "utf-8")

lines = f.read().split("\n")
for line in lines:
    line = line.strip()
    if line == '' or line.find("#") == 0:
        continue

    iface, func, params, exp_status, exp_resp = line.split("|")
    p = json.loads(params)

    status = "ok"

    try:
        svc = getattr(client, iface)
        fn = getattr(svc, func)
        resp = fn(*p)
    except barrister.RpcException as e:
        status = "rpcerr"
        resp = e.code
    except:
        print "ERR: %s" % str(sys.exc_info())
        status = "err"
        resp = ""

    out.write("%s|%s|%s|%s|%s\n" % (iface, func, params, status, json.dumps(resp)))
    line = f.readline()

f.close()
out.close()
