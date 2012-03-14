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

def newUser(userId=None, email=None):
    return { "userId" : userId, "email" : email }

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
        userId = uuid.uuid4()
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
        self.server = runtime.Server(contract)
        self.server.set_interface_handler("UserService", UserServiceImpl())

        transport = runtime.InProcTransport("test")
        transport.serve(self.server)
        self.client = transport.client()

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

class ClientTest(unittest.TestCase):

    def setUp(self):
        contract = runtime.Contract(barrister.parse_str(idl))
        self.server = runtime.Server(contract)
        self.server.set_interface_handler("UserService", UserServiceImpl())
        transport = runtime.InProcTransport("test")
        transport.serve(self.server)
        self.client = transport.client()

    def test_invalid_req(self):
        self.assertRaises(runtime.RpcException, self.client.UserService.get)

if __name__ == "__main__":
    unittest.main()

