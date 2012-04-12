"""
    Parser lib for converting IDL prose into a parsed representation suitable for saving as JSON

    http://barrister.bitmechanic.com/

    :copyright: 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""

import time
import copy
import operator
import cStringIO
from plex import Scanner, Lexicon, Str, State, IGNORE, Begin, Any, AnyBut, AnyChar, Range, Rep
try:
    import json
except:
    import simplejson as json

def md5(s):
    try:
        import hashlib
        return hashlib.md5(s).hexdigest()
    except:
        import md5
        return md5.new(s).hexdigest()

native_types = [ "int", "float", "string", "bool" ]
letter       = Range("AZaz")
digit        = Range("09")
under        = Str("_")
ident        = letter + Rep(letter | digit | under)
arr_ident    = Str("[]") + ident
space        = Any(" \t\n\r")
comment      = Str("// ") | Str("//")
type_opts    = Str("[") + Rep(AnyBut("{}]\n")) + Str("]")

def parse(idl_text, name=None, validate=True, add_meta=True):
    if isinstance(idl_text, (str, unicode)):
        idl_text = cStringIO.StringIO(idl_text)

    scanner = IdlScanner(idl_text, name)
    scanner.parse()
    if validate:
        scanner.validate()
    if len(scanner.errors) == 0:
        if add_meta:
            scanner.add_meta()
        return scanner.parsed
    else:
        raise IdlParseException(scanner.errors)

class IdlParseException(Exception):

    def __init__(self, errors):
        Exception.__init__(self)
        self.errors = errors

    def __str__(self):
        s = ""
        for e in self.errors:
            if s != "":
                s += ", "
            s += "line: %d message: %s" % (e["line"], e["message"])
        return s

class IdlScanner(Scanner):

    def eof(self):
        if self.cur:
            self.add_error("Unexpected end of file")

    def add_meta(self):
        import barrister
        meta = {
            "type"              : "meta",
            "barrister_version" : barrister.__version__,
            "date_generated"    : int(time.time() * 1000),
            "checksum"          : self.get_checksum()
        }
        self.parsed.append(meta)

    def get_checksum(self):
        """
        Returns a checksum based on the IDL that ignores comments and ordering,
        but detects changes to types, parameter order, and enum values.
        """
        arr = [ ]
        for elem in self.parsed:
            if elem["type"] == "struct":
                s = ""
                fields = copy.copy(elem["fields"])
                fields.sort(key=operator.itemgetter("name"))
                for f in fields:
                    s += "\t%s\t%s\t%s\t%s" % (f["name"], f["type"], f["is_array"], f["optional"])
                arr.append("struct\t%s\t%s\t%s\n" % (elem["name"], elem["extends"], s))
            elif elem["type"] == "enum":
                s = "enum\t%s" % elem["name"]
                vals = copy.copy(elem["values"])
                vals.sort(key=operator.itemgetter("value"))
                for v in vals: s += "\t%s" % v["value"]
                s += "\n"
                arr.append(s)
            elif elem["type"] == "interface":
                s = "interface\t%s" % elem["name"]
                funcs = copy.copy(elem["functions"])
                funcs.sort(key=operator.itemgetter("name"))
                for f in funcs:
                    s += "[%s" % f["name"]
                    for p in f["params"]:
                        s += "\t%s\t%s" % (p["type"], p["is_array"])
                    ret = f["returns"]
                    s += "(%s\t%s\t%s)]" % (ret["type"], ret["is_array"], ret["optional"])
                s += "\n"
                arr.append(s)
        arr.sort()
        #print arr
        return md5(json.dumps(arr))

    def add_error(self, message, line=-1):
        if line < 0:
            (name, line, col) = self.position()
        self.errors.append({"line": line, "message": message})

    def begin_struct(self, text):
        self.check_dupe_name(text)
        self.cur = { "name" : text, "type" : "struct", "extends" : "",
                     "comment" : self.get_comment(), "fields" : [] }
        self.begin('start-block')

    def begin_enum(self, text):
        self.check_dupe_name(text)
        self.cur = { "name" : text, "type" : "enum", 
                     "comment" : self.get_comment(), "values" : [] }
        self.begin('start-block')

    def begin_interface(self, text):
        self.check_dupe_name(text)
        self.cur = { "name" : text, "type" : "interface", 
                     "comment" : self.get_comment(), "functions" : [] }
        self.begin('start-block')

    def check_dupe_name(self, name):
        if self.types.has_key(name):
            self.add_error("type %s already defined" % name)

    def check_not_empty(self, cur, list_name, printable_name):
        if len(cur[list_name]) == 0:
            self.add_error("%s must have at least one %s" % (cur["name"], printable_name))
            return False
        return True

    def start_block(self, text):
        t = self.cur["type"]
        if t == "struct":
            self.begin("fields")
        elif t == "enum":
            self.begin("values")
        elif t == "interface":
            self.begin("functions")
        else:
            raise Exception("Invalid type: %s" % t)

    def end_block(self, text):
        ok = False
        t = self.cur["type"]
        if t == "struct":
            ok = self.check_not_empty(self.cur, "fields", "field")
        elif t == "enum":
            ok = self.check_not_empty(self.cur, "values", "value")
        elif t == "interface":
            ok = self.check_not_empty(self.cur, "functions", "function")
        
        if ok:
            self.parsed.append(self.cur)
            self.types[self.cur["name"]] = self.cur

        self.cur = None
        self.begin('')

    def begin_field(self, text):
        self.field = { "name" : text }
        self.begin("field")

    def end_field(self, text):
        is_array = False
        if text.find("[]") == 0:
            text = text[2:]
            is_array = True
        self.field["type"] = text
        self.field["is_array"] = is_array
        self.field["comment"] = self.get_comment()
        self.field["optional"] = False
        self.type = self.field
        self.cur["fields"].append(self.field)
        self.field = None
        self.next_state = "fields"
        self.begin("type-opts")

    def begin_function(self, text):
        self.function = { "name" : text, "comment" : self.get_comment(), "params" : [ ] }
        self.begin("function-start")

    def begin_param(self, text):
        self.param = { "name" : text }
        self.begin("param")

    def end_param(self, text):
        is_array = False
        if text.find("[]") == 0:
            text = text[2:]
            is_array = True
        self.param["type"] = text
        self.param["is_array"] = is_array
        self.function["params"].append(self.param)
        self.param = None
        self.begin("end-param")

    def end_return(self, text):
        is_array = False
        if text.find("[]") == 0:
            text = text[2:]
            is_array = True
        self.function["returns"] = { "type": text, "is_array": is_array, "optional": False }
        self.type = self.function["returns"]
        self.next_state = "functions"
        self.cur["functions"].append(self.function)
        self.function = None
        self.begin("type-opts")

    def end_type_opts(self, text):
        text = text.strip()
        if text.startswith("[") and text.endswith("]"):
            text = text[1:-1]
        if text != "":
            if text == "optional":
                self.type["optional"] = True
            else:
                raise Exception("Invalid type option: %s" % text)
        self.type = None
        self.begin(self.next_state)
        self.next_state = None

    def end_type_opts_and_block(self, text):
        self.end_type_opts(text)
        self.end_block(text)

    def end_value(self, text):
        if not text in self.cur["values"]:
            val = { "value" : text, "comment" : self.get_comment() }
            self.last_comment = ""
            self.cur["values"].append(val)

    def get_comment(self):
        comment = ""
        if self.comment and len(self.comment) > 0:
            comment = "".join(self.comment)
        self.comment = None
        return comment

    def start_comment(self, text):
        if self.comment:
            self.comment.append("\n")
        else:
            self.comment = []
        self.prev_state = self.state_name
        self.begin("comment")

    def append_comment(self, text):
        self.comment.append(text)

    def append_field_options(self, text):
        self.field_options.append(text)

    def end_comment(self, text):
        self.begin(self.prev_state)
        self.prev_state = None

    def end_extends(self, text):
        if self.cur and self.cur["type"] == "struct":
            self.cur["extends"] = text
        else:
            self.add_error("extends is only supported for struct types")

    def add_comment_block(self, text):
        comment = self.get_comment()
        if comment:
            self.parsed.append({"type" : "comment", "value" : comment})

    lex = Lexicon([
            (Str("\n"),  add_comment_block),
            (space,      IGNORE),
            (Str('struct '),   Begin('struct-start')),
            (Str('enum '),   Begin('enum-start')),
            (Str('interface '),   Begin('interface-start')),
            (comment,    start_comment),
            State('struct-start', [
                    (ident,    begin_struct),
                    (space,    IGNORE),
                    (AnyChar, "Missing identifier") ]),
            State('enum-start', [
                    (ident,    begin_enum),
                    (space,    IGNORE),
                    (AnyChar, "Missing identifier") ]),
            State('interface-start', [
                    (ident,    begin_interface),
                    (space,    IGNORE),
                    (AnyChar, "Missing identifier") ]),
            State('start-block', [
                    (space, IGNORE),
                    (Str("extends"), Begin('extends')),
                    (Str('{'), start_block) ]),
            State('extends', [
                    (space, IGNORE),
                    (ident, end_extends),
                    (Str('{'), start_block) ]),
            State('fields', [
                    (ident,    begin_field),
                    (space,    IGNORE),
                    (comment, start_comment),
                    (Str('{'), 'invalid'),
                    (Str('}'), end_block) ]),
            State('field', [
                    (ident,    end_field),
                    (arr_ident, end_field),
                    (Str("\n"), 'invalid'),
                    (space,    IGNORE),
                    (Str('{'), 'invalid'),
                    (Str('}'), 'invalid') ]),
            State('functions', [
                    (ident,    begin_function),
                    (space,    IGNORE),
                    (comment,  start_comment),
                    (Str('{'), 'invalid'),
                    (Str('}'), end_block) ]),
            State('function-start', [
                    (Str("("), Begin('params')),
                    (Str("\n"), 'invalid'),
                    (space,    IGNORE) ]),
            State('params', [
                    (ident,    begin_param),
                    (space,    IGNORE),
                    (Str(")"), Begin('function-return')) ]),
            State('end-param', [
                    (space, IGNORE),
                    (Str(","), Begin('params')),
                    (Str(")"), Begin('function-return')) ]),
            State('param', [
                    (ident,    end_param),
                    (arr_ident, end_param),
                    (space,    IGNORE) ]),
            State('function-return', [
                    (space,    IGNORE),
                    (ident,    end_return),
                    (arr_ident, end_return) ]),
            State('type-opts', [
                    (type_opts, end_type_opts),
                    (Str("\n"), end_type_opts),
                    (Str('}'),  end_block),
                    (space,    IGNORE),
                    (Str('{'),  'invalid') ]),
            State('end-function', [
                    (Str("\n"), Begin('functions')),
                    (space, IGNORE) ]),
            State('values', [
                    (ident,    end_value),
                    (space,    IGNORE),
                    (comment,  start_comment),
                    (Str('{'), 'invalid'),
                    (Str('}'), end_block) ]),
            State('comment', [
                    (Str("\n"),     end_comment),
                    (AnyChar, append_comment) ])
            ])

    def __init__(self, f, name):
        Scanner.__init__(self, self.lex, f, name)
        self.parsed = [ ]
        self.errors = [ ]
        self.types = { }
        self.comment = None
        self.cur = None

    def parse(self):
        while True:
            (t, name) = self.read()
            if t is None:
                break
            else:
                self.add_error(t)
                break

    def validate_type(self, cur_type, types, level):
        level += 1

        cur_type = self.strip_array_chars(cur_type)

        if cur_type in native_types or cur_type in types:
            pass
        elif not self.types.has_key(cur_type):
            self.add_error("undefined type: %s" % cur_type, line=0)
        else:
            cur = self.types[cur_type]
            types.append(cur_type)
            if cur["type"] == "struct":
                if cur["extends"] != "":
                    self.validate_type(cur["extends"], types, level)
                for f in cur["fields"]:
                    self.validate_type(f["type"], types, level)
            elif cur["type"] == "interface":
                # interface types must be top-level, so if len(types) > 1, we
                # know this interface was used as a type in a function or struct
                if level > 1:
                    msg = "interface %s cannot be a field type" % cur["name"]
                    self.add_error(msg, line=0)
                else:
                    for f in cur["functions"]:
                        types = [ ]
                        for p in f["params"]:
                            self.validate_type(p["type"], types, 1)
                        self.validate_type(f["returns"]["type"], types, 1)

    def add_parent_fields(self, s, names, types):
        if s["extends"] in native_types:
            self.add_error("%s cannot extend %s" % (s["name"], s["extends"]), line=0)
        elif self.types.has_key(s["extends"]):
            if s["name"] not in types:
                types.append(s["name"])
                parent = self.types[s["extends"]]
                if parent["type"] == "struct":
                    for f in parent["fields"]:
                        if f["name"] not in names:
                            names.append(f["name"])
                    self.add_parent_fields(parent, names, types)
                else:
                    self.add_error("%s cannot extend %s %s" % (s["name"], parent["type"], parent["name"]), line=0)

    def validate_struct_extends(self, s):
        names = []
        self.add_parent_fields(s, names, [])
        for f in s["fields"]:
            if f["name"] in names:
                self.add_error("%s cannot redefine parent field %s" % (s["name"], f["name"]), line=0)

    def contains_cycle(self, name, types):
        name = self.strip_array_chars(name)
        if self.types.has_key(name):
            t = self.types[name]
            if t["type"] == "struct":
                if name in types:
                    self.add_error("cycle detected in: %s %s" % (t["type"], name), line=0)
                    return True
                else:
                    types.append(name)
                    if self.contains_cycle(t["extends"], types):
                        return True
                    for f in t["fields"]:
                        # use a copy of the type list to keep function checks separate
                        if self.contains_cycle(f["type"], types[:]):
                            return True
        return False

    def strip_array_chars(self, name):
        if name.find("[]") == 0:
            return name[2:]
        return name

    def validate(self):
        for t in self.parsed:
            if t["type"] == "comment":
                pass
            elif not self.contains_cycle(t["name"], []):
                self.validate_type(t["name"], [], 0)
                if t["type"] == "struct":
                    self.validate_struct_extends(t)
