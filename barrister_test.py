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
                       "comment" : "", "extends" : "",
                       "fields" : [ { "type" : "string", "name" : "email" },
                                    { "type" : "int", "name" : "age"} ] } ]
        self.assertEquals(expected, parse_str(idl))

    def test_parse_multiple(self):
        idl = """struct Person { email string } 
struct Animal { furry bool }"""
        expected = [ { "name" : "Person", 
                       "type" : "struct", 
                       "comment" : "", "extends" : "",
                       "fields" : [ { "type" : "string", "name" : "email" } ] },
                     { "name" : "Animal", 
                       "type" : "struct", 
                       "comment" : "", "extends" : "",
                       "fields" : [ { "type" : "bool", "name" : "furry" } ] } ]
        self.assertEquals(expected, parse_str(idl))

    def test_parse_enum(self):
        idl = """enum Status { success fail
invalid }"""
        expected = [ { "name" : "Status", "type" : "enum", "comment" : "",
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
                       "comment" : "",
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
        expected = [ { "name" : "Status", "type" : "enum", "comment" : "",
                       "values" : [ { "comment" : "Request successful",
                                      "value": "success" } ] } ]
        self.assertEquals(expected, parse_str(idl))        

    def test_function_comments(self):
        idl = """interface FooService {
     //Add two numbers
     // a is the 1st num
     //  b is the 2nd num
     add(a int, b int) int
}"""
        expected = [ { "name" : "FooService", "type" : "interface", "comment" : "",
                       "functions" : [
                    { "name" : "add", "returns" : "int", 
                      "comment" : "Add two numbers\na is the 1st num\n b is the 2nd num",
                      "params" : [
                            { "type" : "int", "name" : "a" },
                            { "type" : "int", "name" : "b" } ] } ] } ]
        self.assertEquals(expected, parse_str(idl))        

    def test_interface_comments(self):
        idl = """// FooService is a..
// and does other stuff
interface FooService {
    blah99() blah_Response
}"""
        expected = [ { "name" : "FooService", "type" : "interface",
                       "comment" : "FooService is a..\nand does other stuff",
                       "functions" : [
                    { "name" : "blah99", "returns" : "blah_Response",
                      "comment" : "", "params" : [ ] }
                    ] } ]
        self.assertEquals(expected, parse_str(idl))
        

    def test_extends_struct(self):
        idl = """struct Animal {
   color string
   gender string
}

struct Cat extends Animal {
    purr_volume int
}"""
        expected = [ { "name" : "Animal", "type" : "struct", 
                       "extends" : "", "comment" : "",
                       "fields" : [ { "name" : "color", "type" : "string" },
                                    { "name" : "gender", "type" : "string" } ] },
                     { "name" : "Cat", "type" : "struct", 
                       "extends" : "Animal", "comment" : "",
                       "fields" : [ { "name" : "purr_volume", "type" : "int" } ] } ]
        self.assertEquals(expected, parse_str(idl))

if __name__ == "__main__":
    unittest.main()
