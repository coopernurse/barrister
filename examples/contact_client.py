#!/usr/bin/env python

import barrister
import uuid
import random
import sys

########################

# some random names
first_names = [ "Sam", "John", "James", "Zak", "Trevor", "Lori", "Lily", "Minnie" ]
last_names  = [ "Smith", "Doe", "Edwards", "Jacobson", "Myers" ]

def rand_val(arr):
    i = random.randint(0, len(arr)-1)
    return arr[i]

def new_phone(ptype, country, number):
    return { "type"        : ptype,
             "countryCode" : country,
             "number"      : number }

def new_contact(userId, first, last, email, phones=None):
    if not phones:
        phones = [ ]
    return { "contactId" : uuid.uuid4().hex, 
             "userId"    : userId,
             "firstName" : first,
             "lastName"  : last,
             "email"     : email,
             "phones"    : phones }

########################

trans  = barrister.HttpTransport("http://localhost:7186/contact")
client = barrister.Client(trans)

# Two fictional users, Bob and Mary
bobId  = "user-1"
maryId = "user-2"

# Load all contacts for each user and delete them
for userId in (bobId, maryId):
    for c in client.ContactService.getAll(userId):
        print "Deleting contact: %s" % c["contactId"]
        client.ContactService.delete(c["contactId"], userId)

# Create 10 contacts for Bob, which puts him at his limit
bobContactIds = [ ]
for i in range(10):
    email = "email-%s-%d@example.com" % (bobId, i)
    contact = new_contact(bobId, rand_val(first_names), rand_val(last_names), email)
    contactId = client.ContactService.put(contact)
    bobContactIds.append(contactId)

# Try to add one more.  This should fail
try:
    email = "deny_me@example.com"
    contact = new_contact(bobId, rand_val(first_names), rand_val(last_names), email)
    client.ContactService.put(contact)
    print "Darn! Bob is over the limit, but server let him add another anyway!"
    sys.exit(1)
except barrister.RpcException as e:
    # prove that we got the correct error code
    assert(e.code == 102)

# Add 5 contacts for Mary in a batch
maryContactIds = []
batch = client.start_batch()
for i in range(5):
    email = "email-%s-%d@example.com" % (maryId, i)
    contact = new_contact(maryId, rand_val(first_names), rand_val(last_names), email)
    # Note: nothing is returned at this point
    batch.ContactService.put(contact)

result = batch.send()
for i in range(result.count):
    # each result is unmarshaled here, and a RpcException would be thrown
    # if that particular result in the batch failed
    maryContactIds.append(result.get(i))

print "Mary has %d contacts now" % len(maryContactIds)

# Test null responses
contact = client.ContactService.get("not-valid-id", bobId)
assert(contact == None)

# Delete Mary's contacts
for cid in maryContactIds:
    assert(client.ContactService.delete(cid, maryId) == True)

print "Deleted Mary's contacts.."

# Verify that delete on a non-existant contact id returns False
assert(client.ContactService.delete(maryContactIds[0], maryId) == False)

# Verify that Mary can't delete one of Bob's contacts
try:
    client.ContactService.delete(bobContactIds[0], maryId)
except barrister.RpcException as e:
    assert(e.code == 101)

