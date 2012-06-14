#!/usr/bin/env python

"""
    Module for generating Graphviz dot files based on Barrister IDL JSON

    Inspiration:
    http://www.ffnn.nl/pages/articles/media/uml-diagrams-using-graphviz-dot.php

    Graphviz:
    http://www.graphviz.org/

    :copyright: 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""

def type_str(type_dict):
    s = type_dict['type']
    if type_dict.has_key('is_array') and type_dict['is_array']:
        s = s + "[]"
    return s

def struct_dot(struct):
    extends = ""
    if struct.has_key("extends") and struct["extends"]:
        extends = "%s -> %s" % (struct["name"], struct["extends"])
        
    label = "%s|" % struct["name"]
    for f in struct["fields"]:
        label += "+ %s : %s\\l" % (f["name"],  type_str(f))
    return """%s [
        fillcolor = "#f0fff0"
        style = filled
        label = "{%s}"
]

%s
""" % (struct["name"], label, extends)
    
def enum_dot(enum):
    label = "%s\\n(enum)|" % enum["name"]
    for v in enum["values"]:
        label += "%s\\l" % (v["value"])
    return """%s [
            fillcolor = "#e6e6fa"
            style = filled
            label = "{%s}"
    ]
    """ % (enum["name"], label)
    
def interface_dot(iface):
    label = "%s|" % iface["name"]
    for f in iface["functions"]:
        prms = ""
        for p in f["params"]:
            if prms: prms += ", "
            prms += "%s" % type_str(p)
        label += "+ %s(%s) : %s\\l" % (f["name"], prms, type_str(f["returns"]))
    return """%s [
            fillcolor = "#fafad2"
            style = filled
            label = "{%s}"
    ]
    """ % (iface["name"], label)
    
def to_dotfile(parsed_idl):
    dot = """digraph G {
        fontname = "Bitstream Vera Sans"
        fontsize = 8

        node [
                fontname = "Bitstream Vera Sans"
                fontsize = 8
                shape = "record"
        ]

        edge [
                fontname = "Bitstream Vera Sans"
                fontsize = 8
        ]
        
        edge [
                arrowhead = "empty"
        ]
        
        """
    for entity in parsed_idl:
        if entity.has_key("type"):
            t = entity["type"]
            if t == "struct":
                dot += "\n" + struct_dot(entity)
            elif t == "enum":
                dot += "\n" + enum_dot(entity)
            elif t == "interface":
                dot += "\n" + interface_dot(entity)
            

    dot += "}\n"
    return dot

