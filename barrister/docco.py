#!/usr/bin/env python

"""
    Module for generating Docco style HTML output based on a Barrister IDL file.

    See: http://jashkenas.github.com/docco/

    :copyright: 2012 by James Cooper.  Embedded CSS is copyright Jeremy Ashkenas.
    :license: MIT, see LICENSE for more details.
"""

import sys
import markdown
import optparse
try:
    import json
except:
    import simplejson as json

#
# Thank you Jeremy Ashkenas
# http://jashkenas.github.com/docco/
#
DOCCO_CSS="""
/*--------------------- Layout and Typography ----------------------------*/
body {
  font-family: 'Palatino Linotype', 'Book Antiqua', Palatino, FreeSerif, serif;
  font-size: 15px;
  line-height: 22px;
  color: #252519;
  margin: 0; padding: 0;
}
a {
  color: #261a3b;
}
  a:visited {
    color: #261a3b;
  }
p {
  margin: 0 0 15px 0;
}
h1, h2, h3, h4, h5, h6 {
  margin: 0px 0 15px 0;
}
  h1 {
    margin-top: 40px;
  }
#container {
  position: relative;
}
#background {
  position: fixed;
  top: 0; left: 525px; right: 0; bottom: 0;
  background: #f5f5ff;
  border-left: 1px solid #e5e5ee;
  z-index: -1;
}
#jump_to, #jump_page {
  background: white;
  -webkit-box-shadow: 0 0 25px #777; -moz-box-shadow: 0 0 25px #777;
  -webkit-border-bottom-left-radius: 5px; -moz-border-radius-bottomleft: 5px;
  font: 10px Arial;
  text-transform: uppercase;
  cursor: pointer;
  text-align: right;
}
#jump_to, #jump_wrapper {
  position: fixed;
  right: 0; top: 0;
  padding: 5px 10px;
}
  #jump_wrapper {
    padding: 0;
    display: none;
  }
    #jump_to:hover #jump_wrapper {
      display: block;
    }
    #jump_page {
      padding: 5px 0 3px;
      margin: 0 0 25px 25px;
    }
      #jump_page .source {
        display: block;
        padding: 5px 10px;
        text-decoration: none;
        border-top: 1px solid #eee;
      }
        #jump_page .source:hover {
          background: #f5f5ff;
        }
        #jump_page .source:first-child {
        }
table td {
  border: 0;
  outline: 0;
}
  td.docs, th.docs {
    max-width: 450px;
    min-width: 450px;
    min-height: 5px;
    padding: 10px 25px 1px 50px;
    overflow-x: hidden;
    vertical-align: top;
    text-align: left;
  }
    .docs pre {
      margin: 15px 0 15px;
      padding-left: 15px;
    }
    .docs p tt, .docs p code {
      background: #f8f8ff;
      border: 1px solid #dedede;
      font-size: 12px;
      padding: 0 0.2em;
    }
    .pilwrap {
      position: relative;
    }
      .pilcrow {
        font: 12px Arial;
        text-decoration: none;
        color: #454545;
        position: absolute;
        top: 3px; left: -20px;
        padding: 1px 2px;
        opacity: 0;
        -webkit-transition: opacity 0.2s linear;
      }
        td.docs:hover .pilcrow {
          opacity: 1;
        }
  td.code, th.code {
    padding: 14px 15px 16px 25px;
    width: 100%;
    vertical-align: top;
    background: #f5f5ff;
    border-left: 1px solid #e5e5ee;
  }
    pre, tt, code {
      font-size: 12px; line-height: 18px;
      font-family: Menlo, Monaco, Consolas, "Lucida Console", monospace;
      margin: 0; padding: 0;
    }


/*---------------------- Syntax Highlighting -----------------------------*/
td.linenos { background-color: #f0f0f0; padding-right: 10px; }
span.lineno { background-color: #f0f0f0; padding: 0 5px 0 5px; }
body .hll { background-color: #ffffcc }
body .c { color: #408080; font-style: italic }  /* Comment */
body .err { border: 1px solid #FF0000 }         /* Error */
body .k { color: #954121 }                      /* Keyword */
body .o { color: #666666 }                      /* Operator */
body .cm { color: #408080; font-style: italic } /* Comment.Multiline */
body .cp { color: #BC7A00 }                     /* Comment.Preproc */
body .c1 { color: #408080; font-style: italic } /* Comment.Single */
body .cs { color: #408080; font-style: italic } /* Comment.Special */
body .gd { color: #A00000 }                     /* Generic.Deleted */
body .ge { font-style: italic }                 /* Generic.Emph */
body .gr { color: #FF0000 }                     /* Generic.Error */
body .gh { color: #000080; font-weight: bold }  /* Generic.Heading */
body .gi { color: #00A000 }                     /* Generic.Inserted */
body .go { color: #808080 }                     /* Generic.Output */
body .gp { color: #000080; font-weight: bold }  /* Generic.Prompt */
body .gs { font-weight: bold }                  /* Generic.Strong */
body .gu { color: #800080; font-weight: bold }  /* Generic.Subheading */
body .gt { color: #0040D0 }                     /* Generic.Traceback */
body .kc { color: #954121 }                     /* Keyword.Constant */
body .kd { color: #954121; font-weight: bold }  /* Keyword.Declaration */
body .kn { color: #954121; font-weight: bold }  /* Keyword.Namespace */
body .kp { color: #954121 }                     /* Keyword.Pseudo */
body .kr { color: #954121; font-weight: bold }  /* Keyword.Reserved */
body .kt { color: #B00040 }                     /* Keyword.Type */
body .m { color: #666666 }                      /* Literal.Number */
body .s { color: #219161 }                      /* Literal.String */
body .na { color: #7D9029 }                     /* Name.Attribute */
body .nb { color: #954121 }                     /* Name.Builtin */
body .nc { color: #0000FF; font-weight: bold }  /* Name.Class */
body .no { color: #880000 }                     /* Name.Constant */
body .nd { color: #AA22FF }                     /* Name.Decorator */
body .ni { color: #999999; font-weight: bold }  /* Name.Entity */
body .ne { color: #D2413A; font-weight: bold }  /* Name.Exception */
body .nf { color: #0000FF }                     /* Name.Function */
body .nl { color: #A0A000 }                     /* Name.Label */
body .nn { color: #0000FF; font-weight: bold }  /* Name.Namespace */
body .nt { color: #954121; font-weight: bold }  /* Name.Tag */
body .nv { color: #19469D }                     /* Name.Variable */
body .ow { color: #AA22FF; font-weight: bold }  /* Operator.Word */
body .w { color: #bbbbbb }                      /* Text.Whitespace */
body .mf { color: #666666 }                     /* Literal.Number.Float */
body .mh { color: #666666 }                     /* Literal.Number.Hex */
body .mi { color: #666666 }                     /* Literal.Number.Integer */
body .mo { color: #666666 }                     /* Literal.Number.Oct */
body .sb { color: #219161 }                     /* Literal.String.Backtick */
body .sc { color: #219161 }                     /* Literal.String.Char */
body .sd { color: #219161; font-style: italic } /* Literal.String.Doc */
body .s2 { color: #219161 }                     /* Literal.String.Double */
body .se { color: #BB6622; font-weight: bold }  /* Literal.String.Escape */
body .sh { color: #219161 }                     /* Literal.String.Heredoc */
body .si { color: #BB6688; font-weight: bold }  /* Literal.String.Interpol */
body .sx { color: #954121 }                     /* Literal.String.Other */
body .sr { color: #BB6688 }                     /* Literal.String.Regex */
body .s1 { color: #219161 }                     /* Literal.String.Single */
body .ss { color: #19469D }                     /* Literal.String.Symbol */
body .bp { color: #954121 }                     /* Name.Builtin.Pseudo */
body .vc { color: #19469D }                     /* Name.Variable.Class */
body .vg { color: #19469D }                     /* Name.Variable.Global */
body .vi { color: #19469D }                     /* Name.Variable.Instance */
body .il { color: #666666 }                     /* Literal.Number.Integer.Long */
"""

def format_type(t):
    """
    Returns the type as a string.  If the type is an array, then it is prepended with []
    
    :Parameters:
      t
        The type as a dict. Keys: 'type', 'is_array'
    """
    s = ""
    if t.has_key('is_array') and t['is_array']:
        s = "[]%s" % t['type']
    else:
        s = t['type']
    if t.has_key('optional') and t['optional'] == True:
        s += " [optional]"
    return s

def docco_html(title, idl_parsed):
    """
    Translates a parsed Barrister IDL into HTML.  Returns a string containing the HTML.

    :Parameters:
      title
        Title of the document. Will be includined in <title> and <h1> tags
      idl_parsed
        Parsed representation of IDL to convert to HTML
    """
    sections = to_sections(idl_parsed)
    s = """<!DOCTYPE html>
<html>
<head>
  <title>%s</title>
  <meta http-equiv="content-type" content="text/html; charset=UTF-8">
  <style type="text/css">
  %s
  </style>
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
      <tbody>""" % (title, DOCCO_CSS, title)
    
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
    """
    Returns a docco section for the given enum.

    :Parameters:
      enum
        Parsed IDL enum dict. Keys: 'comment', 'name', 'values'
    """
    docs = enum['comment']
    code = '<span class="k">enum</span> <span class="gs">%s</span> {\n' % enum['name']
    for v in enum["values"]:
        if v['comment']:
            for line in v['comment'].split("\n"):
                code += '    <span class="c1">// %s</span>\n' % line
        code += '    <span class="nv">%s</span>\n' % v['value']
    code += "}"

    return to_section(docs, code)

def parse_struct(s):
    """
    Returns a docco section for the given struct.

    :Parameters:
      s
        Parsed IDL struct dict. Keys: 'comment', 'name', 'extends', 'fields'
    """
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
        code += '    <span class="nv">%s</span>%s<span class="kt">%s</span>\n' % (v['name'], pad[:x], format_type(v))
    code += "}"

    return to_section(docs, code)

def parse_interface(iface):
    """
    Returns a docco section for the given interface.

    :Parameters:
      iface
        Parsed IDL interface dict. Keys: 'comment', 'name', 'returns', 'params'
    """
    sections = [ ]
    docs = iface['comment']
    code = '<span class="k">interface</span> <span class="gs">%s</span> {\n' % iface['name']
    for v in iface["functions"]:
        func_code = '    <span class="nf">%s</span>(' % v['name']
        i = 0
        for p in v["params"]:
            if i == 0: i = 1
            else: func_code += ", "
            func_code += '<span class="na">%s</span> <span class="kt">%s</span>' % (p['name'], format_type(p))
        func_code += ') <span class="kt">%s</span>\n' % format_type(v['returns'])
        if v.has_key('comment') and v['comment']:
            if code:
                sections.append(to_section(docs, code))
            docs = v['comment']
            code = func_code
        else:
            code += func_code
    code += "}"

    sections.append(to_section(docs, code))
    return sections

def wrap_code(code):
    """
    Wraps HTML tags around the given source code block

    :Parameters:
      code
        Source code to wrap
    """
    if code:
        return """<div class="highlight"><pre>%s</pre></div>""" % code
    else:
        return ""

def to_section(docs, code):
    """
    Returns a dict with keys: 'docs', 'code'.  docs are converted to markdown. code is converted
    to HTML using wrap_code.

    :Parameters:
      docs
        Documentation for the section in Markdown format
      code
        Source code for the section in plain text
    """
    return { "docs": markdown.markdown(docs), "code": wrap_code(code) }

def to_sections(idl_parsed):
    """
    Iterates through elements in idl_parsed list and returns a list of section dicts.
    Currently elements of type "comment", "enum", "struct", and "interface" are processed.

    :Parameters:
      idl_parsed
        Barrister parsed IDL
    """
    sections = []
    for entity in idl_parsed:
        if entity["type"] == "comment":
            sections.append(to_section(entity["value"], ""))
        elif entity["type"] == "enum":
            sections.append(parse_enum(entity))
        elif entity["type"] == "struct":
            sections.append(parse_struct(entity))
        elif entity["type"] == "interface":
            sections.extend(parse_interface(entity))
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
    print docco_html(options.title, idl_parsed)
