#!/usr/bin/env python

from flask import Flask, make_response, request
import runtime
import logging
import json
import math
import sys

class A(object):

    def add(self, a, b):
        return a+b

    def add_all(self, nums):
        total = 0
        for n in nums:
            total += n
        return total

    def sqrt(self, a):
        return math.sqrt(a)

    def repeat(self, req):
        resp = { "count" : req["count"], "items" : [ ] }
        for i in range(req["count"]):
            resp["items"].append(req["to_repeat"])
        return resp

    def say_hi(self):
        return { "hi" : "hi" }

class B(object):

    def echo(self, s):
        return s

logging.basicConfig(level=logging.WARN)
app = Flask(__name__)

server = runtime.Server(runtime.contract_from_file(sys.argv[1]))
server.add_handler("A", A())
server.add_handler("B", B())

@app.route("/exit")
def exit():
    func = request.environ.get('werkzeug.server.shutdown')
    func()
    sys.stdout.flush()
    return "shutting down"

@app.route("/", methods=["GET","POST"])
def barrister():
    if request.method == "POST":
        iface_name = request.headers["X-Barrister-Interface"]
        func_name  = request.headers["X-Barrister-Function"]
        params     = json.loads(request.data)
        j = json.dumps(server.call(iface_name, func_name, params))
    elif request.method == "GET":
        j = json.dumps(server.contract.idl_parsed, sort_keys=True, indent=4)
    else:
        raise Exception("Unsupported HTTP method: %s" % request.method)

    resp = make_response(j)
    resp.headers['Content-Type'] = "application/json"
    return resp

app.run(debug=True, host="127.0.0.1", port=9233)
