#!/usr/bin/env python

from flask import Flask, request, jsonify
import runtime
import logging
import json

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

@app.route("/book", methods=["POST"])
def book_rpc():
    req = json.loads(request.data)
    return jsonify(book_server.call(req))

app.run(debug=True)


