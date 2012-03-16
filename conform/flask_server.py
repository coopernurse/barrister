#!/usr/bin/env python

from flask import Flask, request, jsonify
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

@app.route("/", methods=["POST"])
def rpc():
    req = json.loads(request.data)
    return jsonify(server.call(req))

app.run(debug=True, host="127.0.0.1", port=9233)
