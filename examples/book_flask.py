#!/usr/bin/env python

from flask import Flask, make_response, request
import runtime
import logging
try:
    import json
except:
    import simplejson as json

class UserService(object):

    def get(self, userId):
        return { "userId" : userId, "password" : "pw", "email" : "foo@bar.com",
                 "emailVerified" : False, "dateCreated" : 1, "age" : 3.3 }

logging.basicConfig(level=logging.WARN)
app = Flask(__name__)

book_server = runtime.Server(runtime.contract_from_file("examples/book.json"))
book_server.set_interface_handler("UserService", UserService())

@app.route("/book", methods=["GET","POST"])
def book():
    if request.method == "POST":
        iface_name = request.headers["X-Barrister-Interface"]
        func_name  = request.headers["X-Barrister-Function"]
        params     = json.loads(request.data)
        j = json.dumps(book_server.call(iface_name, func_name, params))
    elif request.method == "GET":
        j = json.dumps(book_server.contract.idl_parsed, sort_keys=True, indent=4)
    else:
        raise Exception("Unsupported HTTP method: %s" % request.method)

    resp = make_response(j)
    resp.headers['Content-Type'] = "application/json"
    return resp

app.run(debug=True)
