#!/usr/bin/env python

"""
    barrister
    ~~~~~~~~~

    A RPC toolkit for building lightweight reliable services.  Ideal for
    both static and dynamic languages.

    :copyright: (c) 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""

import uuid
import time
import unittest
import barrister
from barrister.parser import parse

idl = """
struct User {
    userId string
    password string
    email string
    emailVerified bool
    dateCreated int
    age float [optional]
}

enum Status {
    ok
    invalid
    error
}

struct Response {
    status Status
    message string
}

struct CountResponse extends Response {
    count int
}

struct CreateUserResponse extends Response {
    userId string
}

struct UserResponse extends Response {
    user User
}

struct UsersResponse extends Response {
    users []User
}

interface UserService {
    get(userId string) UserResponse
    create(user User) CreateUserResponse
    update(user User) Response
    validateEmail(userId string) Response
    changePassword(userId string, oldPass string, newPass string) Response
    countUsers() CountResponse
    getAll(userIds []string) UsersResponse
}
"""

def newUser(userId="abc123", email=None):
    return { "userId" : userId, "password" : u"pw", "email" : email,
      "emailVerified" : False, "dateCreated" : 1, "age" : 3.3 }

def now_millis():
    return int(time.time() * 1000)

class UserServiceImpl(object):

    def __init__(self):
        self.users = { }

    def get(self, userId):
        resp = self._resp("ok", "user created")
        resp["user"] = self.users[userId]
        return resp

    def create(self, user):
        resp = self._resp("ok", "user created")
        userId = uuid.uuid4().hex
        user["dateCreated"] = now_millis()
        resp["userId"] = userId
        self.users[userId] = user
        return resp

    def update(self, user):
        userId = user["userId"]
        self.users[userId] = user
        return self._resp("ok", "user updated")

    def validateEmail(self, userId):
        return self._resp("ok", "user updated")

    def changePassword(self, userId, oldPass, newPass):
        return self._resp("ok", "password updated")

    def countUsers(self):
        resp = self._resp("ok", "ok")
        resp["count"] = len(self.users)
        return resp

    def getAll(self, userIds):
        return { "status": "ok", "message" : "users here", "users": [] }

    def _resp(self, status, message):
        return { "status" : status, "message" : message }

class RuntimeTest(unittest.TestCase):

    def setUp(self):
        contract = barrister.Contract(parse(idl))
        self.user_svc = UserServiceImpl()
        self.server = barrister.Server(contract)
        self.server.add_handler("UserService", self.user_svc)

        transport = barrister.InProcTransport(self.server)
        self.client = barrister.Client(transport)

    def test_add_handler_invalid(self):
        self.assertRaises(barrister.RpcException, self.server.add_handler, "foo", self.user_svc)

    def test_user_crud(self):
        svc = self.client.UserService
        user = newUser(email="foo@example.com")
        del user["age"]  # field is optional
        resp = svc.create(user)
        self.assertTrue(resp["userId"])
        user2 = svc.get(resp["userId"])["user"]
        self.assertEquals(user["email"], user2["email"])
        self.assertTrue(user["dateCreated"] > 0)
        self.assertEquals("ok", svc.changePassword("123", "oldpw", "newpw")["status"])
        self.assertEquals(1, svc.countUsers()["count"])
        svc.getAll([])

    def test_invalid_req(self):
        svc = self.client.UserService
        cases = [ 
            [ svc.get ],  # too few args
            [ svc.get, 1, 2 ], # too many args
            [ svc.get, 1 ], # wrong type
            [ svc.create, None ], # wrong type
            [ svc.create, 1 ], # wrong type
            [ svc.create, { "UserId" : "1" } ], # unknown param
            [ svc.create, { "userId" : 1 } ], # wrong type
            [ svc.getAll, { } ], # wrong type
            [ svc.getAll, [ 1 ] ] # wrong type
            ]
        for c in cases:
            try:
                if len(c) > 1:
                    c[0](c[1])
                else:
                    c[0]()
                self.fail("Expected RpcException for: %s" % str(c))
            except barrister.RpcException:
                pass

    def test_invalid_resp(self):
        svc = self.client.UserService
        responses = [ 
            { }, # missing fields
            { "status" : "blah" }, # invalid enum
            { "status" : "ok", "message" : 1 }, # invalid type
            { "status" : "ok", "message" : "good", "blarg" : True }, # invalid field
            { "status" : "ok", "message" : "good", "user" : { # missing password field
                    "userId" : "123", "email" : "foo@bar.com",
                    "emailVerified" : False, "dateCreated" : 1, "age" : 3.3 } },
            { "status" : "ok", "message" : "good", "user" : { # missing password field
                    "userId" : "123", "email" : "foo@bar.com",
                    "emailVerified" : False, "dateCreated" : 1, "age" : 3.3 } },
            { "status" : "ok", "user" : { # missing message field
                    "userId" : "123", "email" : "foo@bar.com",
                    "emailVerified" : False, "dateCreated" : 1, "age" : 3.3 } }
            ]
        for resp in responses:
            self.user_svc.get = lambda id: resp
            try:
                svc.get("123")
                self.fail("Expected RpcException for response: %s" % str(resp))
            except barrister.RpcException:
                pass

    def test_batch(self):
        batch = self.client.start_batch()
        batch.UserService.create(newUser(userId="1", email="foo@bar.com"))
        batch.UserService.create(newUser(userId="2", email="foo@bar.com"))
        batch.UserService.countUsers()
        results = batch.send()
        self.assertEquals(3, len(results))
        self.assertEquals(results[0].result["message"], "user created")
        self.assertEquals(results[1].result["message"], "user created")
        self.assertEquals(2, results[2].result["count"])

    def _test_bench(self):
        start = time.time()
        stop = start+1
        num = 0
        while time.time() < stop:
            self.client.UserService.countUsers()
            num += 1
        elapsed = time.time() - start
        print "test_bench: num=%d microsec/op=%d" % (num, (elapsed*1000000)/num)

        start = time.time()
        stop = start+1
        num = 0
        while time.time() < stop:
            self.client.UserService.create(newUser())
            num += 1
        elapsed = time.time() - start
        print "test_bench: num=%d microsec/op=%d" % (num, (elapsed*1000000)/num)

if __name__ == "__main__":
    unittest.main()

