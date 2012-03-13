#!/usr/bin/env python

import sys
import markdown
import optparse
try:
    import json
except:
    import simplejson as json

def to_html(title, sections):
    s = """<!DOCTYPE html>
<html>
<head>
  <title>%s</title>
  <meta http-equiv="content-type" content="text/html; charset=UTF-8">
  <link rel="stylesheet" media="all" href="docco.css" />
</head>
<body>
  <div id="container">
    <div id="background"></div>
    <table cellpadding="0" cellspacing="0">
      <thead>
        <tr>
          <th class="docs">
            <h1>
               %s
            </h1>
          </th>
          <th class="code">
          </th>
        </tr>
      </thead>
      <tbody>""" % (title, title)
    
    i = 0
    for sec in sections:
        i += 1
        s += """<tr id="section-%d">
            <td class="docs">
              <div class="pilwrap">
                <a class="pilcrow" href="#section-%d">&#182;</a>
              </div>
              %s
            </td>
            <td class="code">
              %s
            </td>
          </tr>""" % (i, i, sec['docs'], sec['code'])

    s += """</tbody>
    </table>
  </div>
</body>
</html>"""
    return s
    
def parse_enum(enum):
    docs = enum['comment']
    code = '<span class="k">enum</span> <span class="gs">%s</span> {\n' % enum['name']
    for v in enum["values"]:
        if v['comment']:
            for line in v['comment'].split("\n"):
                code += '    <span class="c1">// %s</span>\n' % line
        code += '    <span class="nv">%s</span>\n' % v['value']
    code += "}"

    return docs, code

def parse_struct(s):
    docs = s['comment']
    code = '<span class="k">struct</span> <span class="gs">%s</span>' % s['name']
    if s['extends']:
        code += ' extends <span class="gs">%s</span>' % s['extends']
    code += ' {\n'
    maxlen = 0
    for v in s["fields"]:
        if len(v['name']) > maxlen:
            maxlen = len(v['name'])

    maxlen += 1
    pad = ""
    for i in range(maxlen): pad += " "

    for v in s["fields"]:
        if v.has_key('comment') and v['comment']:
            for line in v['comment'].split("\n"):
                code += '    <span class="c1">// %s</span>\n' % line
        x = maxlen - len(v['name'])
        code += '    <span class="nv">%s</span>%s<span class="kt">%s</span>\n' % (v['name'], pad[:x], v['type'])
    code += "}"

    return docs, code

def parse_interface(iface):
    docs = iface['comment']
    code = '<span class="k">interface</span> <span class="gs">%s</span> {\n' % iface['name']
    for v in iface["functions"]:
        if v.has_key('comment') and v['comment']:
            for line in v['comment'].split("\n"):
                code += '    <span class="c1">// %s</span>\n' % line
        code += '    <span class="nf">%s</span>(' % v['name']
        i = 0
        for p in v["params"]:
            if i == 0: i = 1
            else: code += ", "
            code += '<span class="na">%s</span> <span class="kt">%s</span>' % (p['name'], p['type'])
        code += ') <span class="kt">%s</span>\n' % v['returns']
    code += "}"

    return docs, code

def to_section(entity):
    if entity["type"] == "enum":
        docs, code = parse_enum(entity)
    elif entity["type"] == "struct":
        docs, code = parse_struct(entity)
    elif entity["type"] == "interface":
        docs, code = parse_interface(entity)
    code = """<div class="highlight"><pre>%s</pre></div>""" % code
    return { "docs": markdown.markdown(docs), "code": code }

def to_sections(idl_parsed):
    sections = []
    for entity in idl_parsed:
        sections.append(to_section(entity))
    return sections

if __name__ == "__main__":
    parser = optparse.OptionParser("usage: %prog [options] [json filename]")
    parser.add_option("-i", "--stdin", dest="stdin", action="store_true",
                      default=False, help="Read JSON from STDIN")
    parser.add_option("-t", "--title", dest="title",
                      default="", type="string",
                      help="page title")
    (options, args) = parser.parse_args()

    if options.stdin:
        j = sys.stdin.read()
    elif len(args) < 1:
        parser.error("Incorrect number of args")
    else:
        f = open(args[0])
        j = f.read()
        f.close()

    idl_parsed = json.loads(j)
    sections = to_sections(idl_parsed)
    print to_html(options.title, sections)
