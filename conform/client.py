#!/usr/bin/env python

import sys
import barrister
import codecs
import logging
try:
    import json
except:
    import simplejson as json

logging.basicConfig()
logging.getLogger("barrister").setLevel(logging.DEBUG)

trans    = barrister.HttpTransport("http://localhost:9233/")
client   = barrister.Client(trans, validate_request=False)
batch    = None

f   = open(sys.argv[1])
out = codecs.open(sys.argv[2], "w", "utf-8")

def get_and_log_result(iface, func, params, result, error):
    status = "ok"
    resp   = result
    
    if error != None:
        status = "rpcerr"
        resp = error.code
        print "RPCERR: %s" % error.msg

    out.write("%s|%s|%s|%s|%s\n" % (iface, func, params, status, json.dumps(resp)))
    out.flush()

########################################

lines = f.read().split("\n")
for line in lines:
    line = line.strip()
    if line == '' or line.find("#") == 0:
        continue

    if line == 'start_batch':
        batch = client.start_batch()
        continue
    elif line == 'end_batch':
        results = batch.send()
        for i in range(0, len(results)):
            res = results[i]
            req = res.request
            pos = req["method"].find(".")
            iface = req["method"][:pos]
            func  = req["method"][pos+1:]
            get_and_log_result(iface, func, json.dumps(req["params"]), res.result, res.error)
        batch = None
        continue

    cur_client = client
    if batch:
        cur_client = batch

    iface, func, params, exp_status, exp_resp = line.split("|")
    p = json.loads(params)

    svc = getattr(cur_client, iface)
    fn  = getattr(svc, func)
    if isinstance(p, list):
        c = lambda: fn(*p)
    else:
        c = lambda: fn(p)

    if batch:
        c()
    else:
        result = None
        error  = None
        try:
            result = c()
        except barrister.RpcException as e:
            error = e
        except e:
            error = barrister.RpcException(-1, str(sys.exc_info()))
        get_and_log_result(iface, func, params, result, error)

    line = f.readline()

f.close()
out.close()
