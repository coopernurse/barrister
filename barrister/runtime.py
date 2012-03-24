
import urllib2
import uuid
import sys
import itertools
try:
    import json
except: 
    import simplejson as json

# JSON-RPC standard error codes
ERR_PARSE = -32700
ERR_INVALID_REQ = -32600
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_PARAMS = -32602
ERR_INTERNAL = -32603

# Our extensions
ERR_UNKNOWN = -32000
ERR_INVALID_RESP = -32001

def contract_from_file(fname):
    f = open(fname)
    j = f.read()
    f.close()
    return Contract(json.loads(j))

def unpack_method(method):
    pos = method.find(".")
    if pos == -1:
        raise RpcException(ERR_METHOD_NOT_FOUND, "Method not found: %s" % method)

    iface_name = method[:pos]
    func_name  = method[pos+1:]
    return iface_name, func_name

def idgen_uuid():
    return uuid.uuid4().hex

idgen_seq_counter = itertools.count()
def idgen_seq():
    return str(idgen_seq_counter.next())

class RpcException(Exception, json.JSONEncoder):

    def __init__(self, code, msg="", data=None):
        self.code = code
        self.msg = msg
        self.data = data

    def __str__(self):
        s = "RpcException: code=%d msg=%s" % (self.code, self.msg)
        if self.data:
            s += "%s data=%s" % (s, str(self.data))
        return s

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
            raise RpcException(ERR_INVALID_REQ, "Unknown interface: '%s'", iface_name)

    def call(self, req):
        if isinstance(req, list):
            if len(req) < 1:
                return self._err(None, ERR_INVALID_REQ, "Invalid Request. Empty batch.")

            resp = [ ]
            for r in req:
                resp.append(self._call_and_format(r))
            return resp
        else:
            return self._call_and_format(req)

    def _err(self, reqid, code, msg, data=None):
        err = { "code": code, "message": msg }
        if data:
            err["data"] = data
        return { "jsonrpc": "2.0", "id": reqid, "error": err }
    
    def _call_and_format(self, req):
        if not isinstance(req, dict):
            return self._err(None, ERR_INVALID_REQ, 
                             "Invalid Request. %s is not an object." % str(req))

        reqid = None
        if req.has_key("id"):
            reqid = req["id"]

        try:
            resp = self._call(req)
            return { "jsonrpc": "2.0", "id": reqid, "result": resp }
        except RpcException as e:
            return self._err(reqid, e.code, e.msg, e.data)
        except:
            return self._err(reqid, ERR_UNKNOWN, str(sys.exc_info()))
        

    def _call(self, req):
        if not req.has_key("method"):
            raise RpcException(ERR_INVALID_REQ, "Invalid Request. No 'method'.")

        method = req["method"]

        if method == "barrister-idl":
            return self.contract.idl_parsed

        iface_name, func_name = unpack_method(method)

        if self.handlers.has_key(iface_name):
            iface_impl = self.handlers[iface_name]
            func = getattr(iface_impl, func_name)
            if func:
                if req.has_key("params"):
                    params = req["params"]
                else:
                    params = [ ]

                if self.validate_req:
                    self.contract.validate_request(iface_name, func_name, params)

                if params:
                    result = func(*params)
                else:
                    result = func()

                if self.validate_resp:
                    self.contract.validate_response(iface_name, func_name, result)
                return result
            else:
                msg = "Method '%s' not found" % (method)
                raise RpcException(ERR_METHOD_NOT_FOUND, msg)
        else:
            msg = "No implementation of '%s' found" % (iface_name)
            raise RpcException(ERR_METHOD_NOT_FOUND, msg)        

class HttpTransport(object):

    def __init__(self, url, handlers=None, headers=None):
        if not headers:
            headers = { }
        headers['Content-Type'] = 'application/json'
        self.url = url
        self.headers = headers
        if handlers:
            self.opener = urllib2.build_opener(*handlers)
        else:
            self.opener = urllib2.build_opener()
        
    def request(self, req):
        data = json.dumps(req)
        req = urllib2.Request(self.url, data, self.headers)
        f = urllib2.urlopen(req)
        resp = f.read()
        f.close()
        return json.loads(resp)

class InProcTransport(object):

    def __init__(self, server):
        self.server = server

    def request(self, req):
        return self.server.call(req)

class Client(object):
    
    def __init__(self, transport, validate_request=True, validate_response=True,
                 id_gen=idgen_uuid):
        self.transport = transport
        self.validate_req  = validate_request
        self.validate_resp = validate_response
        self.id_gen = id_gen
        req = {"jsonrpc": "2.0", "method": "barrister-idl", "id": "1"}
        resp = transport.request(req)
        self.contract = Contract(resp["result"])
        for k, v in self.contract.interfaces.items():
            setattr(self, k, InterfaceClientProxy(self, v))

    def call(self, iface_name, func_name, params):
        req  = self.to_request(iface_name, func_name, params)
        resp = self.transport.request(req)
        return self.to_result(iface_name, func_name, resp)

    def to_request(self, iface_name, func_name, params):
        if self.validate_req:
            self.contract.validate_request(iface_name, func_name, params)
            
        method = "%s.%s" % (iface_name, func_name)
        reqid = self.id_gen()
        return { "jsonrpc": "2.0", "id": reqid, "method": method, "params": params }

    def to_result(self, iface_name, func_name, resp):
        if resp.has_key("error"):
            e = resp["error"]
            data = None
            if e.has_key("data"):
                data = e["data"]
            raise RpcException(e["code"], e["message"], data)
            
        result = resp["result"]
        
        if self.validate_resp:
            self.contract.validate_response(iface_name, func_name, result)
        return result

    def start_batch(self):
        return Batch(self)

class InterfaceClientProxy(object):

    def __init__(self, client, iface):
        self.client = client
        iface_name = iface.name
        for func_name, func in iface.functions.items():
            setattr(self, func_name, self._caller(iface_name, func_name))

    def _caller(self, iface_name, func_name):
        def caller(*params):
            return self.client.call(iface_name, func_name, params)
        return caller        

class Batch(object):

    def __init__(self, client):
        self.client = client
        self.req_list = [ ]
        self.sent = False
        for k, v in client.contract.interfaces.items():
            setattr(self, k, InterfaceClientProxy(self, v))

    def call(self, iface_name, func_name, params):
        if self.sent:
            raise Exception("Batch already sent. Cannot add more calls.")
        else:
            req = self.client.to_request(iface_name, func_name, params)
            self.req_list.append(req)

    def send(self):
        if self.sent:
            raise Exception("Batch already sent. Cannot send() again.")
        else:
            resp = self.client.transport.request(self.req_list)
            self.sent = True
            return BatchResult(self, self.req_list, resp)

class BatchResult(object):

    def __init__(self, batch, req_list, resp):
        if len(req_list) != len(resp):
            msg = "Batch response length %d != request %d" % (len(resp), len(req_list))
            raise RpcException(ERR_INVALID_RESP, msg)

        self.id_to_method = { }
        by_id = { }
        for r in resp:
            reqid = r["id"]
            by_id[reqid] = r

        in_req_order = [ ]
        for r in req_list:
            reqid = r["id"]
            if not by_id.has_key(reqid):
                msg = "Batch response missing result for request id: %s" % reqid
                raise RpcException(ERR_INVALID_RESP, msg)
            in_req_order.append(by_id[reqid])
            self.id_to_method[reqid] = r["method"]

        self.batch = batch
        self.resp = in_req_order
        self.count = len(in_req_order)

    def get(self, i):
        if i < self.count:
            resp = self.resp[i]
            method = self.id_to_method[resp["id"]]
            iface_name, func_name = unpack_method(method)
            return self.batch.client.to_result(iface_name, func_name, resp)
        else:
            raise IndexError("%d >= result size: %d" % (i, self.count))

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
            raise RpcException(ERR_INVALID_PARAMS, "Unknown entity: '%s'", name)

    def struct(self, struct_name):
        if self.structs.has_key(struct_name):
            return self.structs[struct_name]
        else:
            raise RpcException(ERR_INVALID_PARAMS, "Unknown struct: '%s'", struct_name)

    def has_interface(self, iface_name):
        return self.interfaces.has_key(iface_name)

    def interface(self, iface_name):
        if self.has_interface(iface_name):
            return self.interfaces[iface_name]
        else:
            raise RpcException(ERR_INVALID_PARAMS, "Unknown interface: '%s'", iface_name)

    def validate(self, expected_type, is_array, val, allow_missing=True):
        if is_array:
            if not isinstance(val, list):
                return self._type_err(val, "list")
            else:
                for v in val:
                    ok, msg = self.validate(expected_type, False, v, allow_missing)
                    if not ok:
                        return ok, msg
        elif expected_type == "int":
            if not isinstance(val, (long, int)):
                return self._type_err(val, "int")
        elif expected_type == "float":
            if not isinstance(val, (float, int, long)):
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

    def _type_err(self, val, expected):
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
            raise RpcException(ERR_METHOD_NOT_FOUND, 
                               "%s: Unknown function: '%s'", self.name, func_name)

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
                ok, msg = self.contract.validate(field["type"], field["is_array"],
                                                 v, allow_missing)
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
        plen = 0
        if params != None:
            plen = len(params)

        if len(self.params) != plen:
            vals = (self.full_name, len(self.params), plen)
            raise RpcException(ERR_INVALID_PARAMS,
                               "Function '%s' expects %d param(s). %d given." % vals)
        
        if params != None:
            i = 0
            for p in self.params:
                self.validate(p, params[i])
                i += 1

    def validate_response(self, resp):
        ok, msg = self.contract.validate(self.returns, False, resp, allow_missing=False)
        if not ok:
            vals = (self.full_name, str(resp), msg)
            msg = "Function '%s' invalid response: '%s'. %s" % vals
            raise RpcException(ERR_INVALID_RESP, msg)

    def validate(self, expected, param):
        ok, msg = self.contract.validate(expected["type"], expected["is_array"], param)
        if not ok:
            vals = (self.full_name, expected["name"], msg)
            msg = "Function '%s' invalid param '%s'. %s" % vals
            raise RpcException(ERR_INVALID_PARAMS, msg)
