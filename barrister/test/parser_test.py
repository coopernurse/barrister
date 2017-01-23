#!/usr/bin/env python

"""
    barrister
    ~~~~~~~~~

    A RPC toolkit for building lightweight reliable services.  Ideal for
    both static and dynamic languages.

    :copyright: (c) 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""

import os
import os.path
import inspect
import time
import unittest
from barrister.parser import parse, file_paths, IdlParseException

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
        self.assertEqual(expected, parse(idl, add_meta=False))

    def test_parse_struct(self):
        idl = """struct Person {
email string
age int
}"""
        expected = [ { "name" : "Person", 
                       "type" : "struct", 
                       "comment" : "", "extends" : "",
                       "fields" : [ field("email", "string"), field("age", "int") ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))

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
        self.assertEqual(expected, parse(idl, add_meta=False))

    def test_parse_enum(self):
        idl = """enum Status { success fail
invalid }"""
        expected = [ { "name" : "Status", "type" : "enum", "comment" : "",
                       "values" : [ { "value" : "success", "comment" : "" },
                                    { "value" : "fail", "comment" : "" },
                                    { "value" : "invalid", "comment" : "" } ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))

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
        self.assertEqual(expected, parse(idl, add_meta=False, validate=False))

    def test_invalid_struct(self):
        idl = """struct foo { """
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "Unexpected end of file" } ]
            self.assertEqual(expected, e.errors)

    def test_missing_name(self):
        idls = [ "struct  {", "enum {", "interface { " ]
        for idl in idls:
            try:
                parse(idl, add_meta=False)
                self.fail("should have thrown exception")
            except IdlParseException as e:
                expected = [ { "line": 1, "message" : "Missing identifier" } ]
                self.assertEqual(expected, e.errors)

    def test_enum_comments(self):
        idl = """enum Status {
     // Request successful
     success }"""
        expected = [ { "name" : "Status", "type" : "enum", "comment" : "",
                       "values" : [ { "comment" : "Request successful",
                                      "value": "success" } ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))        

    def test_array_type(self):
        idl = """struct Animal  {
    friend_names []string }"""
        expected = [ { "name" : "Animal", "type" : "struct", "comment" : "",
                       "extends" : "",
                 "fields" : [ field("friend_names", "string", "", True) ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))

    def test_array_return_type(self):
        idl = """interface FooService {
    repeat(s string) []string
}"""
        expected = [ { "name" : "FooService", "type" : "interface", "comment" : "",
                       "functions" : [
                    { "name" : "repeat",  "comment" : "",
                      "returns" : ret_field("string", True),
                      "params" : [ { "type" : "string", "name" : "s", "is_array": False } ] } ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))

    def test_struct_comments(self):
        idl = """struct Animal   {
     // fur color
     color string }"""
        expected = [ { "name" : "Animal", "type" : "struct", "comment" : "",
                       "extends" : "",
                       "fields" : [ field("color", "string", "fur color") ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))        

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
        self.assertEqual(expected, parse(idl, add_meta=False))        

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
        self.assertEqual(expected, parse(idl, add_meta=False, validate=False))
        

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
        self.assertEqual(expected, parse(idl, add_meta=False))

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
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 4, "message" : "type Animal already defined" },
                         { "line": 10, "message" : "type Foo already defined" },
                         { "line": 14, "message" : "type Blarg already defined" } ]
            self.assertEqual(expected, e.errors)

    def test_no_cycles_for_required_fields(self):
        idl = """struct Animal {
    home Location
}
struct Location {
    resident Animal
}"""
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 3, "message" : "cycle detected in struct: Animal" },
                         { "line": 6, "message" : "cycle detected in struct: Location" } ]
            self.assertEqual(expected, e.errors)

    def test_slice_cycle_ok(self):
        idl = """struct Animal {
    home Location
}
struct Location {
    residents []Animal
}"""
        parse(idl, add_meta=False)

    def test_optional_cycle_ok(self):
        idl = """struct Animal {
    home Location
}
struct Location {
    resident Animal [optional]
}"""
        parse(idl, add_meta=False)
            
    def test_no_cycles_extends_field(self):
        idl = """struct Animal extends Location {
    home int
}
struct Location {
    residents Animal
}"""
        try:
          parse(idl, add_meta=False)
          self.fail("should have thrown exception")
        except IdlParseException as e:
          expected = [ { "line": 3, "message" : "cycle detected in struct: Animal" },
                       { "line": 6, "message" : "cycle detected in struct: Location" } ]
          self.assertEqual(expected, e.errors)

    def test_no_mutual_extends(self):
        idl = """struct Animal extends Location {
    home int
}
struct Location extends Animal {
    age int
}
"""
        try:
          parse(idl, add_meta=False)
          self.fail("should have thrown exception")
        except IdlParseException as e:
          expected = [ { "line": 3, "message" : "cycle detected in struct: Animal" },
                       { "line": 6, "message" : "cycle detected in struct: Location" } ]
          self.assertEqual(expected, e.errors)

    def test_cycle_detection(self):
        idl = """struct Book {
    author string
}
struct TaskResult {
    toLoan []Book
    toAck  []Book
}"""
        parse(idl, add_meta=False)

    def test_interface_cant_be_field_type(self):
        idl = """struct Animal {
    svc FooService
}
interface FooService {
    do_something() bool
}"""
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 2, "message" : "interface FooService cannot be used as a type" } ]
            self.assertEqual(expected, e.errors)        

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
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 2, "message" : "undefined type: Color" },
                         { "line": 5, "message" : "undefined type: Cat" },
                         { "line": 5, "message" : "undefined type: Saying" },
                         { "line": 7, "message" : "Blarg extends unknown type Foo" } ]
            self.assertEqual(expected, e.errors)
            
    def test_ident_can_start_with_underscores(self):
        idl = """struct Animal { 
    _id int
    _name string
}"""
        expected = [ { "name" : "Animal", "type" : "struct", 
                       "extends" : "", "comment" : "",
                       "fields" : [ field("_id", "int"), 
                                    field("_name", "string") ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))

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
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 6, "message" : "Cat cannot redefine parent field color" },
                         { "line": 9, "message" : "Manx cannot redefine parent field gender" } ]
            self.assertEqual(expected, e.errors)

    def test_struct_cant_extend_enum(self):
        idl = """enum Status { foo }
struct Animal extends Status {
    color string
}"""
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 2, "message" : "Animal cannot extend enum Status" } ]
            self.assertEqual(expected, e.errors)        

    def test_struct_cant_extend_native_type(self):
        idl = """struct Animal extends float {
    color string
}"""
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "Animal cannot extend float" } ]
            self.assertEqual(expected, e.errors)        

    def test_struct_must_have_fields(self):
        idl = "struct Animal { }"
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "Animal must have at least one field" } ]
            self.assertEqual(expected, e.errors)        

    def test_interface_must_have_funcs(self):
        idl = "interface FooService { }"
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "FooService must have at least one function" } ]
            self.assertEqual(expected, e.errors)        

    def test_enum_must_have_values(self):
        idl = "enum Status { }"
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 1, "message" : "Status must have at least one value" } ]
            self.assertEqual(expected, e.errors)        

    def test_cycle_detection_for_interfaces(self):
        idl = """struct BaseResponse {
    status int
}
interface FooService {
    add(a int, b int) BaseResponse
    subtract(a int, b int) BaseResponse
}"""
        # should work - cycle detection should reset per function
        parse(idl, add_meta=False)

    def test_interface_cant_be_param(self):
        idl = """interface BlargService {
    do_stuff() int
}
interface FooService {
    add(a int, b BlargService) float
    subtract(a int, b int) BlargService
}"""
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 5, "message" : "interface BlargService cannot be used as a type" },
                         { "line": 6, "message" : "interface BlargService cannot be used as a type" } ]
            self.assertEqual(expected, e.errors)        

    def test_optional_struct_field(self):
        idl = """struct Person {
   firstName string
   email string  [optional]
}"""
        expected = [ { "name" : "Person", "type" : "struct", 
                       "extends" : "", "comment" : "",
                       "fields" : [ field("firstName", "string"), 
                                    field("email", "string", optional=True) ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))

    def test_optional_return_type(self):
        idl = """interface FooService {
   sayHi() string [optional]
}"""
        expected = [ { "name": "FooService", "type": "interface", "comment": "",
                       "functions" : 
                       [ { "name" : "sayHi", "comment" : "", "params" : [ ],
                           "returns" : ret_field("string", optional=True) } ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))

    def test_prefix_namespace_if_present(self):
      idl = """
      namespace common

    struct A {
      f1    int
      b1    B
    }

    struct B {
      s1    string
    }

    struct C extends common.B {
      b1    bool
    }

    struct D {
       a1    common.A
       c1    C
       dir   SortDir
    }

    enum SortDir {
        ASC
        DESC
    }
    """
      expected = [ { "name" : "common.A", "type" : "struct", 
                       "extends" : "", "comment" : "",
                       "fields" : [ field("f1", "int"), 
                                    field("b1", "common.B") ] },
                    { "name" : "common.B", "type" : "struct", 
                       "extends" : "", "comment" : "",
                       "fields" : [ field("s1", "string") ] },
                    { "name" : "common.C", "type" : "struct", 
                       "extends" : "common.B", "comment" : "",
                       "fields" : [ field("b1", "bool") ] },
                    { "name" : "common.D", "type" : "struct", 
                       "extends" : "", "comment" : "",
                       "fields" : [ field("a1", "common.A"), 
                                    field("c1", "common.C"),
                                    field("dir", "common.SortDir") ] },
                    { "name" : "common.SortDir", "type" : "enum", 
                      "comment" : "",
                      "values" : [ 
                          { "comment" : "", "value": "ASC" },
                          { "comment" : "", "value": "DESC" }
                      ] }
      ]
      self.assertEqual(expected, parse(idl, validate=False, add_meta=False))

    def test_cannot_namespace_interfaces(self):
        idl = """namespace foo

interface FooService {
  doStuff() bool
}
        """
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 3, "message" : "namespace cannot be used in files with interfaces" } ]
            self.assertEqual(expected, e.errors)

    def test_cannot_redefine_namespace(self):
        idl = """namespace foo
namespace bar
        """
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 2, "message" : "Cannot redeclare namespace" } ]
            self.assertEqual(expected, e.errors)

    def test_namespace_must_preceed_elems(self):
        idl = """enum Status { 
        A
        B
        }

namespace foo

struct Blah { 
    name string
}
        """
        try:
            parse(idl, add_meta=False)
            self.fail("should have thrown exception")
        except IdlParseException as e:
            expected = [ { "line": 6, "message" : "namespace must preceed all struct/enum/interface definitions" } ]
            self.assertEqual(expected, e.errors)  

    def test_add_meta(self):
        idl = """interface FooService {
    do_foo() string
}"""
        start = int(time.time() * 1000)
        parsed = parse(idl, add_meta=True)
        meta = parsed[-1]
        generated = meta["date_generated"]
        checksum = meta["checksum"]
        stop = int(time.time() * 1000)
        self.assertTrue(generated >= start and generated <= stop)
        self.assertTrue(checksum != None)

    def test_meta_checksum(self):
        base = "enum Y {\ndog\ncat\n}\nstruct Z {\n a int }\n"
        base2 = "// foo\nstruct Z {\n //foo2\na int }\nenum Y {\ncat\ndog\n}\n"
        equivalent = [ base+"interface FooService {\n  do_foo() string\n}",
                       "interface FooService {\n  do_foo() string\n}"+base2,
                       base+" interface  FooService  {\n  // stuff\n do_foo() string\n\n}" ]
        first_checksum = None
        for idl in equivalent:
            parsed = parse(idl, add_meta=True)
            meta = parsed[-1]
            checksum = meta["checksum"]
            if first_checksum == None:
                first_checksum = checksum
            else:
                self.assertEqual(first_checksum, checksum)

        base3 = "enum Y {\ndog2\ncat\n}\nstruct Z {\n a int }\n"
        base4 = "enum Y {\ndog\ncat\n}\nstruct Z {\n a float }\n"
        different = [ base3+"interface FooService {\n  do_foo() string\n}",
                      base4+"interface FooService {\n  do_foo() string\n}",
                      base+"interface FooService {\n  do_foo(a int) string\n}",
                      base+"interface FooService {\n  do_foo(a int) string\n do_bar() int\n}",
                      base+"// foo interface\n interface  FooService  {\n  // stuff\n do_foo() float\n\n}" ]
        for idl in different:
            parsed = parse(idl, add_meta=True)
            meta = parsed[-1]
            self.assertNotEqual(first_checksum, meta["checksum"])

    def test_file_paths(self):
      # [0] = relative filename
      # [1] = search path dirs
      # [2] = expected paths returned

      # set BARRISTER_TEST, which should be used if no search path is provided
      os.environ["BARRISTER_PATH"] = "/dir1" + os.pathsep + "/dir2"
      tests = [
        [ "a.idl", "/tmp" + os.pathsep + "/usr/local", [ "a.idl", "/tmp" + os.sep + "a.idl", "/usr/local" + os.sep + "a.idl"] ],
        [ "../b.idl", None, [ "../b.idl", "/dir1" + os.sep + "../b.idl", "/dir2" + os.sep + "../b.idl" ] ]
      ]
      for test in tests:
        paths = file_paths(test[0], test[1])
        self.assertEqual(test[2], paths)

      # remove BARRISTER_PATH and re-test
      del os.environ["BARRISTER_PATH"]
      tests = [
        [ "a.idl", "/tmp" + os.pathsep + "/usr/local", [ "a.idl", "/tmp" + os.sep + "a.idl", "/usr/local" + os.sep + "a.idl"] ],
        [ "../b.idl", None, [ "../b.idl" ] ]
      ]
      for test in tests:
        paths = file_paths(test[0], test[1])
        self.assertEqual(test[2], paths)

    def test_notification_type(self):
        idl = """interface FooService {
    notifyThis(s string)
}"""
        expected = [ { "name" : "FooService", "type" : "interface", "comment" : "",
                       "functions" : [
                    { "name" : "notifyThis",  "comment" : "",
                      "params" : [ { "type" : "string", "name" : "s", "is_array": False } ] } ] } ]
        self.assertEqual(expected, parse(idl, add_meta=False))

if __name__ == "__main__":
    unittest.main()
