#!/usr/bin/env python

from flask import Flask, request, make_response
import barrister
import logging
import json
import math
import sys

class A(object):

    def add(self, a, b):
        return a+b

    def calc(self, nums, op):
        total = 0
        if op == "multiply":
            total = 1
            
        for n in nums:
            if op == "add":
                total += n
            elif op == "multiply":
                total = total * n
            else:
                raise Exception("Unknown op: " + op)
        return total

    def sqrt(self, a):
        return math.sqrt(a)

    def repeat(self, req):
        resp = { "status" : "ok", "count" : req["count"], "items" : [ ] }
        s = req["to_repeat"]
        if req["force_uppercase"]:
            s = s.upper()
        for i in range(req["count"]):
            resp["items"].append(s)
        return resp

    def repeat_num(self, num, count):
        l = [ ]
        for i in range(count):
            l.append(num)
        return l

    def say_hi(self):
        return { "hi" : "hi" }

class B(object):

    def echo(self, s):
        return s

logging.basicConfig(level=logging.WARN)
app = Flask(__name__)

server = barrister.Server(barrister.contract_from_file(sys.argv[1]))
server.add_handler("A", A())
server.add_handler("B", B())

@app.route("/exit")
def exit():
    func = request.environ.get('werkzeug.server.shutdown')
    func()
    sys.stdout.flush()
    return "shutting down"

@app.route("/", methods=["POST"])
def rpc():
    #print request.data
    req = json.loads(request.data)
    resp_data = server.call(req)
    #print "Resp: %s" % str(resp_data)
    resp = make_response(json.dumps(resp_data))
    resp.headers['Content-Type'] = 'application/json'
    return resp

app.run(debug=True, host="127.0.0.1", port=9233)
