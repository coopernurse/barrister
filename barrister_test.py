#!/usr/bin/env python

import unittest
from barrister import parse_str, IdlParseException

class BarristerTest(unittest.TestCase):

    def test_parse_struct(self):
        idl = """struct Person {
email string
age int
}"""
        expected = [ { "name" : "Person", 
                       "type" : "struct", 
                       "fields" : [ { "type" : "string", "name" : "email" },
                                    { "type" : "int", "name" : "age"} ] } ]
        self.assertEquals(expected, parse_str(idl))

    def test_parse_multiple(self):
        idl = """struct Person { email string } 
struct Animal { furry bool }"""
        expected = [ { "name" : "Person", 
                       "type" : "struct", 
                       "fields" : [ { "type" : "string", "name" : "email" } ] },
                     { "name" : "Animal", 
                       "type" : "struct", 
                       "fields" : [ { "type" : "bool", "name" : "furry" } ] } ]
        self.assertEquals(expected, parse_str(idl))

    def test_parse_enum(self):
        idl = """enum Status { success fail
invalid }"""
        expected = [ { "name" : "Status", "type" : "enum",
                       "values" : [ "success", "fail", "invalid" ] } ]
        self.assertEquals(expected, parse_str(idl))

    def test_parse_interface(self):
        idl = """interface MyService {
    add(a int, b int) int
    login(req LoginRequest) LoginResponse
}
"""
        expected = [ { "name" : "MyService", 
                       "type" : "interface",
                       "functions" : [
                    { "name" : "add", "returns" : "int", "params" : [
                            { "type" : "int", "name" : "a" },
                            { "type" : "int", "name" : "b" } ] },
                    { "name" : "login", "returns" : "LoginResponse", "params" : [
                            { "type" : "LoginRequest", "name" : "req" } ] } ] } ]
        self.assertEquals(expected, parse_str(idl))

    def test_invalid_struct(self):
        idl = """struct foo { """
        try:
            parse_str(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "Unexpected end of file" } ]
            self.assertEquals(expected, e.errors)

    def test_missing_name(self):
        idls = [ "struct  {", "enum {", "interface { " ]
        for idl in idls:
            try:
                parse_str(idl)
                self.fail("should have thrown exception")
            except IdlParseException as e:
                expected = [ { "line": 1, "message" : "Missing identifier" } ]
                self.assertEquals(expected, e.errors)

if __name__ == "__main__":
    unittest.main()
