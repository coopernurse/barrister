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
        user = { "userId" : userId, "name" : "Bob", "email" : "", 
                 "dateCreated" : 123, "points" : 10,
                 "kindleEmail" : "", "nookEmail" : "", "emailOptIn" : False }
        return { "status" : "success", "message" : "here's your user", "user" : user}

logging.basicConfig(level=logging.WARN)
app = Flask(__name__)

book_server = runtime.Server(runtime.contract_from_file("book.json"))
book_server.add_handler("UserService", UserService())

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
