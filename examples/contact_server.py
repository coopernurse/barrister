#!/usr/bin/env python

import uuid
import logging
import barrister
from bottle import post, request, response, run

#############################

# Define some constants for our error codes
ERR_INVALID = 100
ERR_DENIED  = 101
ERR_LIMIT   = 102

class ContactService(object):

    def __init__(self):
        self.contacts = { }

    def put(self, contact):
        contactId = self._get_or_create_id(contact, "contactId")
        if not self.contacts.has_key(contactId):
            userId = contact["userId"]
            if len(self.getAll(userId)) >= 10:
                # This RpcException will be automatically marshaled and re-thrown
                # on the client side
                msg = "User %s is at the 10 contact limit" % userId
                raise barrister.RpcException(ERR_LIMIT, msg)
        self.contacts[contactId] = contact
        return contactId

    def get(self, contactId, userId):
        if self.contacts.has_key(contactId):
            c = self.contacts[contactId]
            if c["userId"] != userId:
                msg = "userId %s doesn't own contact" % userId
                raise barrister.RpcException(ERR_DENIED, msg)
            else:
                return c
        else:
            return None

    def getAll(self, userId):
        arr = [ ]
        for cid, c in self.contacts.items():
            if c["userId"] == userId:
                arr.append(c)
        return arr

    def delete(self, contactId, userId):
        if self.get(contactId, userId) != None:
            del self.contacts[contactId]
            return True
        else:
            return False

    def _get_or_create_id(self, d, key):
        if not d.has_key(key) or d[key] == "":
            d[key] = uuid.uuid4().hex
        return d[key]

#############################

#
# Our single URL handler for this interface
#
@post('/contact')
def contact():
    # Read the raw POST data 
    data = request.body.read()

    # Hand the request to the Barrister Server object
    # It will call the correct function on the ContactService
    resp_json = server.call_json(data)

    # Set the MIME type, and return the response
    response.content_type = 'application/json'
    return resp_json

if __name__ == '__main__':
    # initialize the Python logger. totally optional.
    logging.basicConfig()

    # load the IDL JSON and create a barrister.Contract object
    contract = barrister.contract_from_file("contact.json")

    # create a Server that will dispatch requests for this Contract
    server = barrister.Server(contract)

    # register our class with the "ContactService" interface
    server.add_handler("ContactService", ContactService())

    # Starts the Bottle app
    run(host='localhost', port=7186)
