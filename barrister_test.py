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
                       "values" : [ { "value" : "success", "comment" : "" },
                                    { "value" : "fail", "comment" : "" },
                                    { "value" : "invalid", "comment" : "" } ] } ]
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
                    { "name" : "add", "comment" : "", "returns" : "int", "params" : [
                            { "type" : "int", "name" : "a" },
                            { "type" : "int", "name" : "b" } ] },
                    { "name" : "login", "comment" : "",
                      "returns" : "LoginResponse", "params" : [
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

    def test_enum_comments(self):
        idl = """enum Status {
     // Request successful
     success }"""
        expected = [ { "name" : "Status", "type" : "enum",
                       "values" : [ { "comment" : "Request successful",
                                      "value": "success" } ] } ]
        self.assertEquals(expected, parse_str(idl))        

    def test_function_comments(self):
        idl = """interface FooService {
     //Add two numbers
     // a is the first num
     //  b is the 2nd num
     add(a int, b int) int
}"""
        expected = [ { "name" : "FooService", "type" : "interface",
                       "functions" : [
                    { "name" : "add", "returns" : "int", 
                      "comment" : "Add two numbers\na is the first num\n b is the 2nd num",
                      "params" : [
                            { "type" : "int", "name" : "a" },
                            { "type" : "int", "name" : "b" } ] } ] } ]
        self.assertEquals(expected, parse_str(idl))        

if __name__ == "__main__":
    unittest.main()
