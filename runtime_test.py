#!/usr/bin/env python

import uuid
import time
import unittest
import barrister
import runtime

idl = """
struct User {
    userId string
    password string
    email string
    emailVerified bool
    dateCreated int
    age float
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

interface UserService {
    get(userId string) UserResponse
    create(user User) CreateUserResponse
    update(user User) Response
    validateEmail(userId string) Response
    changePassword(userId string, oldPass string, newPass string) Response
    countUsers() CountResponse
}
"""

def newUser(userId="abc123", email=None):
    return { "userId" : userId, "password" : "pw", "email" : email,
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

    def _resp(self, status, message):
        return { "status" : status, "message" : message }

class InProcTest(unittest.TestCase):

    def setUp(self):
        contract = runtime.Contract(barrister.parse_str(idl))
        self.user_svc = UserServiceImpl()
        self.server = runtime.Server(contract)
        self.server.add_handler("UserService", self.user_svc)

        transport = runtime.InProcTransport(self.server)
        self.client = transport.client()

    def test_add_handler_invalid(self):
        self.assertRaises(runtime.RpcException, self.server.add_handler, "foo", self.user_svc)

    def test_user_crud(self):
        svc = self.client.UserService
        user = newUser(email="foo@example.com")
        resp = svc.create(user)
        self.assertTrue(resp["userId"])
        user2 = svc.get(resp["userId"])["user"]
        self.assertEquals(user["email"], user2["email"])
        self.assertTrue(user["dateCreated"] > 0)
        self.assertEquals("ok", svc.changePassword("123", "oldpw", "newpw")["status"])
        self.assertEquals(1, svc.countUsers()["count"])

    def test_invalid_req(self):
        svc = self.client.UserService
        cases = [ 
            [ svc.get ],  # too few args
            [ svc.get, 1, 2 ], # too many args
            [ svc.get, 1 ], # wrong type
            [ svc.create, None ], # wrong type
            [ svc.create, 1 ], # wrong type
            [ svc.create, { "UserId" : "1" } ], # unknown param
            [ svc.create, { "userId" : 1 } ] # wrong type
            ]
        for c in cases:
            self.assertRaises(runtime.RpcException, *c)

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
            except runtime.RpcException:
                pass

if __name__ == "__main__":
    unittest.main()

