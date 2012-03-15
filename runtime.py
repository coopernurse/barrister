
try:
    import json
except:
    import simplejson as json

def contract_from_file(fname):
    f = open(fname)
    j = f.read()
    f.close()
    return Contract(json.loads(j))

class RpcException(Exception):
    pass

class Server(object):

    def __init__(self, contract, validate_request=True, validate_response=True):
        self.validate_req  = validate_request
        self.validate_resp = validate_response
        self.contract = contract
        self.handlers = { }

    def add_handler(self, iface_name, handler):
        if self.contract.has_interface(iface_name):
            self.handlers[iface_name] = handler
        else:
            raise RpcException("Unknown interface: '%s'", iface_name)

    def call(self, iface_name, func_name, params):
        if self.handlers.has_key(iface_name):
            iface_impl = self.handlers[iface_name]
            func = getattr(iface_impl, func_name)
            if func:
                if self.validate_req:
                    self.contract.validate_request(iface_name, func_name, params)

                if params:
                    resp = func(*params)
                else:
                    resp = func()

                if self.validate_resp:
                    self.contract.validate_response(iface_name, func_name, resp)
                return resp
            else:
                msg = "Function '%s.%s' not found" % (iface_name, func_name)
                raise RpcException(msg)
        else:
            msg = "No implementation of '%s' found" % (iface_name)
            raise RpcException(msg)        

class InProcTransport(object):

    def __init__(self, server, validate_request=True, validate_response=True):
        self.validate_req  = validate_request
        self.validate_resp = validate_response
        self.server = server

    def client(self):
        return Client(self, self.server.contract, 
                      validate_request=self.validate_req,
                      validate_response=self.validate_resp)
        
    def call(self, iface_name, func_name, params):
        return self.server.call(iface_name, func_name, params)

class Client(object):
    
    def __init__(self, transport, contract, 
                 validate_request=True, validate_response=True):
        self.transport = transport
        self.contract  = contract
        self.validate_req  = validate_request
        self.validate_resp = validate_response
        for k, v in self.contract.interfaces.items():
            setattr(self, k, InterfaceClientProxy(self, v))

class InterfaceClientProxy(object):

    def __init__(self, client, iface):
        self.client = client
        iface_name = iface.name
        for func_name, func in iface.functions.items():
            setattr(self, func_name, self._caller(iface_name, func_name))

    def _caller(self, iface_name, func_name):
        def caller(*params):
            if self.client.validate_req:
                self.client.contract.validate_request(iface_name, func_name, params)
            resp = self.client.transport.call(iface_name, func_name, params)
            if self.client.validate_resp:
                self.client.contract.validate_response(iface_name, func_name, resp)
            return resp
        return caller

class Contract(object):

    def __init__(self, idl_parsed):
        self.idl_parsed = idl_parsed
        self.interfaces = { }
        self.structs = { }
        self.enums = { }
        for e in idl_parsed:
            if e["type"] == "struct":
                self.structs[e["name"]] = Struct(e, self)
            elif e["type"] == "enum":
                self.enums[e["name"]] = Enum(e)
            elif e["type"] == "interface":
                self.interfaces[e["name"]] = Interface(e, self)

    def validate_request(self, iface_name, func_name, params):
        self.interface(iface_name).function(func_name).validate_params(params)

    def validate_response(self, iface_name, func_name, resp):
        self.interface(iface_name).function(func_name).validate_response(resp)

    def get(self, name):
        if self.structs.has_key(name):
            return self.structs[name]
        elif self.enums.has_key(name):
            return self.enums[name]
        elif self.interfaces.has_key(name):
            return self.interfaces[name]
        else:
            raise RpcException("Unknown entity: '%s'", name)

    def struct(self, struct_name):
        if self.structs.has_key(struct_name):
            return self.structs[struct_name]
        else:
            raise RpcException("Unknown struct: '%s'", struct_name)

    def has_interface(self, iface_name):
        return self.interfaces.has_key(iface_name)

    def interface(self, iface_name):
        if self.has_interface(iface_name):
            return self.interfaces[iface_name]
        else:
            raise RpcException("Unknown interface: '%s'", iface_name)

    def validate(self, expected_type, val, allow_missing=True):
        if expected_type == "int":
            if not isinstance(val, (long, int)):
                return self._type_err(val, "int")
        elif expected_type == "float":
            if not isinstance(val, float):
                return self._type_err(val, "float")
        elif expected_type == "bool":
            if not isinstance(val, bool):
                return self._type_err(val, "bool")
        elif expected_type == "string":
            if not isinstance(val, (str, unicode)):
                return self._type_err(val, "string")
        else:
            return self.get(expected_type).validate(val, allow_missing)
        return True, None

    def _type_err(self, expected, val):
        return False, "'%s' is of type %s, expected %s" % (val, type(val), expected)

class Interface(object):

    def __init__(self, iface, contract):
        self.name = iface["name"]
        self.functions = { }
        for f in iface["functions"]:
            self.functions[f["name"]] = Function(self.name, f, contract)

    def function(self, func_name):
        if self.functions.has_key(func_name):
            return self.functions[func_name]
        else:
            raise RpcException("%s: Unknown function: '%s'", self.name, func_name)

class Enum(object):

    def __init__(self, enum):
        self.name = enum["name"]
        self.values = [ ]
        for v in enum["values"]:
            self.values.append(v["value"])

    def validate(self, val, allow_missing):
        if val in self.values:
            return True, None
        else:
            return False, "'%s' is not in enum: %s" % (val, str(self.values))

class Struct(object):

    def __init__(self, s, contract):
        self.contract = contract
        self.name = s["name"]
        self.extends = s["extends"]
        self.parent = None
        self.fields = { }
        for f in s["fields"]:
            self.fields[f["name"]] = f

    def field(self, name):
        if self.fields.has_key(name):
            return self.fields[name]
        elif self.extends:
            if not self.parent:
                self.parent = self.contract.struct(self.extends)
            return self.parent.field(name)
        else:
            return None

    def validate(self, val, allow_missing):
        if type(val) is not dict:
            return False, "%s is not a dict" % (str(val))

        for k, v in val.items():
            field = self.field(k)
            if allow_missing and v == None:
                pass
            elif field:
                ok, msg = self.contract.validate(field["type"], v, allow_missing)
                if not ok:
                    return False, "field '%s': %s" % (field["name"], msg)
            else:
                return False, "field '%s' not found in struct %s" % (k, self.name)

        if not allow_missing:
            for k, v in self.fields.items():
                if not val.has_key(k):
                    return False, "field '%s' missing from: %s" % (k, str(val))

        return True, None

class Function(object):

    def __init__(self, iface_name, f, contract):
        self.contract = contract
        self.name = f["name"]
        self.params = f["params"]
        self.returns = f["returns"]
        self.full_name = "%s.%s" % (iface_name, self.name)
        
    def validate_params(self, params):
        if len(self.params) != len(params):
            vals = (self.full_name, len(self.params), len(params))
            raise RpcException("Function '%s' expects %d param(s). %d given." % vals)
        i = 0
        for p in self.params:
            self.validate(p, params[i])
            i += 1

    def validate_response(self, resp):
        ok, msg = self.contract.validate(self.returns, resp, allow_missing=False)
        if not ok:
            vals = (self.full_name, str(resp), msg)
            msg = "Function '%s' invalid response: '%s'. %s" % vals
            raise RpcException(msg)

    def validate(self, expected, param):
        ok, msg = self.contract.validate(expected["type"], param)
        if not ok:
            vals = (self.full_name, expected["name"], msg)
            msg = "Function '%s' invalid param '%s'. %s" % vals
            raise RpcException(msg)
