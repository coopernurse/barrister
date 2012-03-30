#!/usr/bin/env python

"""
    barrister
    ~~~~~~~~~

    A RPC toolkit for building lightweight reliable services.  Ideal for
    both static and dynamic languages.

    :copyright: (c) 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""

import unittest
from barrister.parser import parse, IdlParseException

def ret_field(type_, is_array=False, optional=False):
    return { "type": type_, "is_array": is_array, "optional": optional }

def field(name, type_, comment="", is_array=False, optional=False):
    return { "type": type_, "name": name, "comment": comment, "is_array": is_array, "optional":  optional}

class ParserTest(unittest.TestCase):

    def test_parse_comment(self):
        idl = """
// # section
// foo

// this is a person
struct Person {
   age int
}"""
        expected = [ { "type" : "comment", "value" : "# section\nfoo" },
                     { "type" : "struct", "name" : "Person", "extends" : "",
                       "comment" : "this is a person", "fields" : [
                    field("age", "int") ] } ]
        self.assertEquals(expected, parse(idl))

    def test_parse_struct(self):
        idl = """struct Person {
email string
age int
}"""
        expected = [ { "name" : "Person", 
                       "type" : "struct", 
                       "comment" : "", "extends" : "",
                       "fields" : [ field("email", "string"), field("age", "int") ] } ]
        self.assertEquals(expected, parse(idl))

    def test_parse_multiple(self):
        idl = """struct Person { email string } 
struct Animal { furry bool }"""
        expected = [ { "name" : "Person", 
                       "type" : "struct", 
                       "comment" : "", "extends" : "",
                       "fields" : [ field("email", "string") ] },
                     { "name" : "Animal", 
                       "type" : "struct", 
                       "comment" : "", "extends" : "",
                       "fields" : [ field("furry", "bool") ] } ]
        self.assertEquals(expected, parse(idl))

    def test_parse_enum(self):
        idl = """enum Status { success fail
invalid }"""
        expected = [ { "name" : "Status", "type" : "enum", "comment" : "",
                       "values" : [ { "value" : "success", "comment" : "" },
                                    { "value" : "fail", "comment" : "" },
                                    { "value" : "invalid", "comment" : "" } ] } ]
        self.assertEquals(expected, parse(idl))

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
                    { "name" : "add", "comment" : "", "returns" : ret_field("int"), 
                      "params" : [
                            { "type" : "int", "name" : "a", "is_array": False },
                            { "type" : "int", "name" : "b", "is_array": False } ] },
                    { "name" : "login", "comment" : "",
                      "returns" : ret_field("LoginResponse"), "params" : [
                            { "type" : "LoginRequest", "name" : "req", "is_array": False } ] } ] } ]
        self.assertEquals(expected, parse(idl, validate=False))

    def test_invalid_struct(self):
        idl = """struct foo { """
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "Unexpected end of file" } ]
            self.assertEquals(expected, e.errors)

    def test_missing_name(self):
        idls = [ "struct  {", "enum {", "interface { " ]
        for idl in idls:
            try:
                parse(idl)
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
        self.assertEquals(expected, parse(idl))        

    def test_array_type(self):
        idl = """struct Animal  {
    friend_names []string }"""
        expected = [ { "name" : "Animal", "type" : "struct", "comment" : "",
                       "extends" : "",
                 "fields" : [ field("friend_names", "string", "", True) ] } ]
        self.assertEquals(expected, parse(idl))

    def test_array_return_type(self):
        idl = """interface FooService {
    repeat(s string) []string
}"""
        expected = [ { "name" : "FooService", "type" : "interface", "comment" : "",
                       "functions" : [
                    { "name" : "repeat",  "comment" : "",
                      "returns" : ret_field("string", True),
                      "params" : [ { "type" : "string", "name" : "s", "is_array": False } ] } ] } ]
        self.assertEquals(expected, parse(idl))

    def test_struct_comments(self):
        idl = """struct Animal   {
     // fur color
     color string }"""
        expected = [ { "name" : "Animal", "type" : "struct", "comment" : "",
                       "extends" : "",
                       "fields" : [ field("color", "string", "fur color") ] } ]
        self.assertEquals(expected, parse(idl))        

    def test_function_comments(self):
        idl = """interface FooService {
     //Add two numbers
     // a is the 1st num
     //  b is the 2nd num
     add(a int, b []int) int
}"""
        expected = [ { "name" : "FooService", "type" : "interface", "comment" : "",
                       "functions" : [
                    { "name" : "add", "returns" : ret_field("int"), 
                      "comment" : "Add two numbers\na is the 1st num\n b is the 2nd num",
                      "params" : [ 
                            { "type" : "int", "name" : "a", "is_array": False },
                            { "type" : "int", "name" : "b", "is_array": True } ] } ] } ]
        self.assertEquals(expected, parse(idl))        

    def test_interface_comments(self):
        idl = """// FooService is a..
// and does other stuff
interface FooService {
    blah99() blah_Response
}"""
        expected = [ { "name" : "FooService", "type" : "interface",
                       "comment" : "FooService is a..\nand does other stuff",
                       "functions" : [
                    { "name" : "blah99", "returns" : ret_field("blah_Response"),
                      "comment" : "", "params" : [ ] }
                    ] } ]
        self.assertEquals(expected, parse(idl, validate=False))
        

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
                       "fields" : [ field("color", "string"), field("gender", "string") ] },
                     { "name" : "Cat", "type" : "struct", 
                       "extends" : "Animal", "comment" : "",
                       "fields" : [ field("purr_volume", "int") ] } ]
        self.assertEquals(expected, parse(idl))

    def test_no_dupe_types(self):
        idl = """struct Animal {
    color string
}
enum Animal {
    foo
}
interface Foo {
    doSomething() bool
}
struct Foo {
    color string
}
enum Blarg {  stuff }
interface Blarg {
    do_other() bool
}"""
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 4, "message" : "type Animal already defined" },
                         { "line": 10, "message" : "type Foo already defined" },
                         { "line": 14, "message" : "type Blarg already defined" } ]
            self.assertEquals(expected, e.errors)

    def test_no_cycles(self):
        idl = """struct Animal {
    home Location
}
struct Location {
    residents []Animal
}"""
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 0, "message" : "cycle detected in: struct Animal" },
                         { "line": 0, "message" : "cycle detected in: struct Location" } ]
            self.assertEquals(expected, e.errors)

    def test_cycle_detection(self):
        idl = """struct Book {
    author string
}
struct TaskResult {
    toLoan []Book
    toAck  []Book
}"""
        parse(idl)

    def test_interface_cant_be_field_type(self):
        idl = """struct Animal {
    svc FooService
}
interface FooService {
    do_something() bool
}"""
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 0, "message" : "interface FooService cannot be a field type" } ]
            self.assertEquals(expected, e.errors)        

    def test_types_exist(self):
        idl = """struct Animal {
    color Color
}
interface FooService {
    saySomething(cat Cat) Saying
}
struct Blarg extends Foo {
   a int
}"""
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 0, "message" : "undefined type: Color" },
                         { "line": 0, "message" : "undefined type: Cat" },
                         { "line": 0, "message" : "undefined type: Saying" },
                         { "line": 0, "message" : "undefined type: Foo" } ]
            self.assertEquals(expected, e.errors)

    def test_cant_override_parent_field(self):
        idl = """struct Animal {
    color string
    gender string
}
struct Cat    extends Animal {
   color int
}
struct Manx extends Cat {
   gender bool
}"""
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 0, "message" : "Cat cannot redefine parent field color" },
                         { "line": 0, "message" : "Manx cannot redefine parent field gender" } ]
            self.assertEquals(expected, e.errors)

    def test_struct_cant_extend_enum(self):
        idl = """enum Status { foo }
struct Animal extends Status {
    color string
}"""
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 0, "message" : "Animal cannot extend enum Status" } ]
            self.assertEquals(expected, e.errors)        

    def test_struct_cant_extend_native_type(self):
        idl = """struct Animal extends float {
    color string
}"""
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 0, "message" : "Animal cannot extend float" } ]
            self.assertEquals(expected, e.errors)        

    def test_struct_must_have_fields(self):
        idl = "struct Animal { }"
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "Animal must have at least one field" } ]
            self.assertEquals(expected, e.errors)        

    def test_interface_must_have_funcs(self):
        idl = "interface FooService { }"
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "FooService must have at least one function" } ]
            self.assertEquals(expected, e.errors)        

    def test_enum_must_have_values(self):
        idl = "enum Status { }"
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "Status must have at least one value" } ]
            self.assertEquals(expected, e.errors)        

    def test_cycle_detection_for_interfaces(self):
        idl = """struct BaseResponse {
    status int
}
interface FooService {
    add(a int, b int) BaseResponse
    subtract(a int, b int) BaseResponse
}"""
        # should work - cycle detection should reset per function
        parse(idl)

    def test_interface_cant_be_param(self):
        idl = """interface BlargService {
    do_stuff() int
}
interface FooService {
    add(a int, b BlargService) float
    subtract(a int, b int) BlargService
}"""
        try:
            parse(idl)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 0, "message" : "interface BlargService cannot be a field type" },
                         { "line": 0, "message" : "interface BlargService cannot be a field type" } ]
            self.assertEquals(expected, e.errors)        

    def test_optional_struct_field(self):
        idl = """struct Person {
   firstName string
   email string  [optional]
}"""
        expected = [ { "name" : "Person", "type" : "struct", 
                       "extends" : "", "comment" : "",
                       "fields" : [ field("firstName", "string"), 
                                    field("email", "string", optional=True) ] } ]
        self.assertEquals(expected, parse(idl))

    def test_optional_return_type(self):
        idl = """interface FooService {
   sayHi() string [optional]
}"""
        expected = [ { "name": "FooService", "type": "interface", "comment": "",
                       "functions" : 
                       [ { "name" : "sayHi", "comment" : "", "params" : [ ],
                           "returns" : ret_field("string", optional=True) } ] } ]
        self.assertEquals(expected, parse(idl))

if __name__ == "__main__":
    unittest.main()
