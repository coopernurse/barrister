#!/usr/bin/env python

from subprocess import Popen, PIPE
import time
import threading
import unittest
import os
import urllib2
import codecs
try:
    import json
except:
    import simplejson as json

# Barrister conformance test runner

def env_get(envkey, defval):
    if os.environ.has_key(envkey):
        return os.environ[envkey]
    else:
        return defval

home = os.environ["HOME"]

#
# resolve homes
barrister_java = env_get("BARRISTER_JAVA", "../../barrister-java")
barrister_node = env_get("BARRISTER_NODE", "../../barrister-js")
barrister_php  = env_get("BARRISTER_PHP", "../../barrister-php")
barrister_ruby = env_get("BARRISTER_RUBY", "../../barrister-ruby")
barrister_go   = env_get("GOPATH", "") + "/src/github.com/coopernurse/barrister-go"

#
# Java config
#
m2_jackson = "%s/.m2/repository/org/codehaus/jackson" % home
jackson_deps = [ "jackson-mapper-asl/1.9.4/jackson-mapper-asl-1.9.4.jar",
                 "jackson-core-asl/1.9.4/jackson-core-asl-1.9.4.jar" ]
java_cp = "%s/target/classes%s%s/conform/target/classes" % (barrister_java, os.pathsep, barrister_java)
for d in jackson_deps:
    java_cp += "%s%s/%s" % (os.pathsep, m2_jackson, d)
java_jar = "%s/conform/target/barrister-conform-test-1.0-SNAPSHOT-with-deps.jar" % barrister_java

java_cp = java_cp.replace("/", os.sep)
java_jar = java_jar.replace("/", os.sep)

#
# Clients to run against each server
#
clients = [ 
    # format: name, command line
    [ "python-client", ["python", "client.py"] ],
    [ "java-client", ["java", "-cp", java_cp, "com.bitmechanic.barrister.conform.Client" ] ],
    [ "node-client", ["node", "%s/conform/client.js" % barrister_node ] ],
    [ "php-client",  ["php", "%s/conform/client.php" % barrister_php ] ],
    [ "ruby-client", ["ruby", "-rubygems", "%s/conform/client.rb" % barrister_ruby ] ],
    [ "go-client", ["%s/conform/client" % barrister_go ] ]
]

verbose = os.environ.has_key('CONFORM_VERBOSE')

def log(msg):
    if verbose:
        print msg.strip()

class Runner(threading.Thread):

    def __init__(self, name, cmd, cwd=None):
        super(Runner, self).__init__()
        self.name = name
        self.cmd = cmd
        self.cwd = cwd
        self.exit_code = None
        self.proc = None

    def terminate(self):
        self.proc.terminate()
        #time.sleep(.1)
        #if not self.proc.returncode:
        #    self.proc.kill()

    def run(self):
        log("[%s] Starting process: %s" % (self.name, " ".join(self.cmd)))
        self.proc = Popen(self.cmd, stdout=PIPE, stderr=PIPE, close_fds=False,
                          shell=False, cwd=self.cwd)
	log("[%s] waiting for proc to end" % self.name)
        out, err = self.proc.communicate()
        outd = Drain("%s out" % self.name, out)
        errd = Drain("%s err" % self.name, err)
        outd.start()
        errd.start()
        outd.join()
        errd.join()
	log("[%s] waiting for proc.poll()" % self.name)
        self.exit_code = self.proc.poll()
	log("[%s] got exit_code=%d" % (self.name, self.exit_code))

class Drain(threading.Thread):

    def __init__(self, name, stream):
        super(Drain, self).__init__()
        self.name = name
        self.stream = stream

    def run(self):
        for line in self.stream.split("\n"):
            log("[%s] %s" %(self.name, line))
        
class ConformTest(unittest.TestCase):

    def test_python_server(self):
        cmd = ["python", "-u", "flask_server.py", "conform.json"]
        self._test_server(1, "python-flask", cmd)

    def test_java_server(self):
        cmd = ["java", "-DidlJson=conform.json", 
               "-cp", java_jar, "com.bitmechanic.barrister.conform.App" ]
        self._test_server(2, "java", cmd)

    def test_node_server(self):
        cmd = ["node", "%s/conform/server.js" % barrister_node ]
        self._test_server(1, "node", cmd)

    def test_php_server(self):
        cmd = ["python", "%s/conform/webserver.py" % barrister_php, "9233" ]
        self._test_server(1, "php", cmd, cwd="%s/conform" % barrister_php)

    def test_ruby_server(self):
        cmd = ["ruby", "-rubygems", "%s/conform/server.rb" % barrister_ruby, "-p", "9233" ]
        self._test_server(2, "ruby", cmd)

    def test_go_server(self):
        cmd = ["%s/conform/server" % barrister_go, "conform.json"]
        self._test_server(2, "go", cmd)

    def _test_invalid_json(self):
        headers = { "Content-Type" : "application/json" }
        invalid = [ "{", "[", "--" ]
        for s in invalid:
            data = """{ "jsonrpc": "2.0", "method": "foo", "params": %s }""" % s
            req = urllib2.Request("http://localhost:9233/", data, headers)
            f = urllib2.urlopen(req)
            json_resp = f.read()
            f.close()
            try:
                resp = json.loads(json_resp)
            except:
                print "Unable to parse: %s" % json_resp
                raise
            self.assertEquals(resp["error"]["code"], -32700, "Fail using invalid JSON: %s" % s)

    def _test_server(self, sleep_time, s_name, s_cmd, cwd=None):
        errs = [ ]
        expected = [ ]
        infile = "conform.in"
        inf = codecs.open(infile, "r", "utf-8")
        for line in inf:
            line = line.strip()
            if line != "" and line.find("#") != 0 and len(line.split("|")) == 5:
                expected.append(line)
        inf.close()
        try:
            s_proc = Runner(s_name, s_cmd, cwd=cwd)
            s_proc.start()
            time.sleep(sleep_time)

            self._test_invalid_json()

            for c_name, c_cmd in clients:
                print "Testing client '%s' vs server '%s'" % (c_name, s_name)
                outfile = "%s-to-%s.out" % (c_name, s_name)
                c_cmd_cpy = c_cmd[:]
                c_cmd_cpy.extend([infile, outfile])
                c_proc = Runner(c_name, c_cmd_cpy)
                c_proc.start()
                c_proc.join()
                if c_proc.exit_code != 0:
                    errs.append("client %s failed - %d" % (c_name, c_proc.exit_code))
                else:
                    out = codecs.open(outfile, "r", "utf-8")
                    i = 0
                    fails = []
                    for line in out:
                        e_cols = expected[i].split("|")
                        l_cols = line.split("|")
                        match = True
                        #print expected[i]
                        #print line
                        if len(e_cols) != len(l_cols):
                            match = False
                        elif e_cols[3] != l_cols[3]:
                            match = False
                        elif json.loads(e_cols[4]) != json.loads(l_cols[4]):
                            match = False
                        if not match:
                            msg = "line %d: %s != %s" % (i, expected[i], line)
                            fails.append(msg)
                            #print msg
                        i += 1
                        if i > len(expected):
                            break
                    out.close()
                    if len(fails) > 0:
                        err = (outfile, len(fails), fails[0])
                        self.fail("%s had %d mismatches. first=%s" % err)
                    elif len(expected) != i:
                        err = (i, len(expected))
                        self.fail("client produced %d lines - expected %d" % err)
        finally:
            s_proc.terminate()
            s_proc.join()
            if len(errs) > 0:
                self.fail("\n".join(errs))
            
if __name__ == "__main__":
    if not verbose:
        print "Verbose output disabled. To enable: export CONFORM_VERBOSE=1"
    unittest.main()
