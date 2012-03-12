
from plex import Scanner, Lexicon, Str, State, IGNORE, Begin, Any, AnyChar, Range, Rep
import cStringIO

letter = Range("AZaz")
digit = Range("09")
under = Str("_")
ident = letter + Rep(letter | digit | under)
arr_ident = Str("[]") + ident
space = Any(" \t\n\r")

class IdlParseException(Exception):

    def __init__(self, errors):
        Exception.__init__(self)
        self.errors = errors

class IdlScanner(Scanner):

    def eof(self):
        if self.cur:
            self.add_error("Unexpected end of file")

    def add_error(self, message):
        (name, line, col) = self.position()
        self.errors.append({"line": line, "message": message})

    def begin_struct(self, text):
        self.cur = { "name" : text, "type" : "struct", "fields" : [] }
        self.begin('start-block')

    def begin_enum(self, text):
        self.cur = { "name" : text, "type" : "enum", "values" : [] }
        self.begin('start-block')

    def begin_interface(self, text):
        self.cur = { "name" : text, "type" : "interface", "functions" : [] }
        self.begin('start-block')

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
        self.parsed.append(self.cur)
        self.cur = None
        self.begin('')

    def begin_field(self, text):
        self.field = { "name" : text }
        self.begin("field")

    def end_field(self, text):
        self.field["type"] = text
        self.cur["fields"].append(self.field)
        self.field = None
        self.begin("fields")

    def begin_function(self, text):
        self.function = { "name" : text, "params" : [ ] }
        self.begin("function-start")

    def begin_param(self, text):
        self.param = { "name" : text }
        self.begin("param")

    def end_param(self, text):
        self.param["type"] = text
        self.function["params"].append(self.param)
        self.param = None
        self.begin("end-param")

    def end_return(self, text):
        self.function["returns"] = text
        self.cur["functions"].append(self.function)
        self.function = None
        self.begin("end-function")

    def end_value(self, text):
        if not text in self.cur["values"]:
            self.cur["values"].append(text)

    lex = Lexicon([
            (space,      IGNORE),
            (Str('struct '),   Begin('struct-start')),
            (Str('enum '),   Begin('enum-start')),
            (Str('interface '),   Begin('interface-start')),
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
                    (Str('{'), start_block) ]),
                    
            State('fields', [
                    (ident,    begin_field),
                    (space,    IGNORE),
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
            State('end-function', [
                    (Str("\n"), Begin('functions')),
                    (space, IGNORE) ]),
            State('values', [
                    (ident,    end_value),
                    (space,    IGNORE),
                    (Str('{'), 'invalid'),
                    (Str('}'), end_block) ])
            ])

    def __init__(self, f, name):
        Scanner.__init__(self, self.lex, f, name)
        self.parsed = [ ]
        self.errors = [ ]
        self.cur = None

    def parse(self):
        while True:
            (t, name) = self.read()
            if t is None:
                break
            else:
                self.add_error(t)
                break


def parse_str(idl):
    reader = cStringIO.StringIO(idl)
    scanner = IdlScanner(reader, "")
    scanner.parse()
    if len(scanner.errors) == 0:
        return scanner.parsed
    else:
        raise IdlParseException(scanner.errors)
    
