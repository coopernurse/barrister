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

home = os.environ["HOME"]


#
# Java config
#
m2_jackson = "%s/.m2/repository/org/codehaus/jackson" % home
jackson_deps = [ "jackson-mapper-asl/1.9.4/jackson-mapper-asl-1.9.4.jar",
                 "jackson-core-asl/1.9.4/jackson-core-asl-1.9.4.jar" ]
barrister_java = "../../barrister-java"
if os.environ.has_key("BARRISTER_JAVA"):
    barrister_java = os.environ["BARRISTER_JAVA"]
java_cp = "%s/target/classes:%s/conform/target/classes" % (barrister_java, barrister_java)
for d in jackson_deps:
    java_cp += ":%s/%s" % (m2_jackson, d)
winstone_jar = "%s/conform/lib/winstone-0.9.10.jar" % barrister_java
java_war = "%s/conform/target/barrister-conform-test.war" % barrister_java


#
# Clients to run against each server
#
clients = [ 
    # format: name, command line
    [ "python-client", ["python", "client.py"] ],
    [ "java-client", ["java", "-cp", java_cp, "com.bitmechanic.barrister.conform.Client" ] ]
]

verbose = os.environ.has_key('CONFORM_VERBOSE')
def log(msg):
    if verbose:
        print msg.strip()

class Runner(threading.Thread):

    def __init__(self, name, cmd):
        super(Runner, self).__init__()
        self.name = name
        self.cmd = cmd
        self.exit_code = None
        self.proc = None

    def run(self):
        log("[%s] Starting process: %s" % (self.name, " ".join(self.cmd)))
        self.proc = Popen(self.cmd, stdout=PIPE, stderr=PIPE, close_fds=False, 
                          shell=False)
        out, err = self.proc.communicate()
        for line in out.split("\n"):
            log("[%s out] %s" % (self.name, line))
        for line in err.split("\n"):
            log("[%s err] %s" % (self.name, line))
        self.exit_code = self.proc.poll()
        
class ConformTest(unittest.TestCase):

    def test_python_server(self):
        cmd = ["python", "flask_server.py", "conform.json"]
        self._test_server(1, "python-flask", cmd)

    def test_java_server(self):
        cmd = ["java", "-DidlJson=conform.json", "-jar", winstone_jar, 
               "--httpPort=9233", java_war ]
        self._test_server(3, "java", cmd)

    def _test_server(self, sleep_time, s_name, s_cmd):
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
            s_proc = Runner(s_name, s_cmd)
            s_proc.start()
            time.sleep(sleep_time)
            for c_name, c_cmd in clients:
                print "Testing client '%s' vs server '%s'" % (c_name, s_name)
                outfile = "%s-to-%s.out" % (c_name, s_name)
                c_cmd.extend([infile, outfile])
                c_proc = Runner(c_name, c_cmd)
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
            r = urllib2.urlopen("http://localhost:9233/exit")
            r.read()
            r.close()
            s_proc.join()
            if len(errs) > 0:
                self.fail("\n".join(errs))
            
if __name__ == "__main__":
    unittest.main()
