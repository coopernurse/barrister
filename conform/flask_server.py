#!/usr/bin/env python

from flask import Flask, request, jsonify
import barrister
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
        resp = { "status" : "ok", "count" : req["count"], "items" : [ ] }
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
    return jsonify(server.call(req))

app.run(debug=True, host="127.0.0.1", port=9233)
