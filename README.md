# Barrister

Barrister lets you write well documented services that can be consumed from a variety of languages.  
The basic steps are:

* Write an IDL file (See: http://barrister.bitmechanic.com/docs.html)
* Run the `barrister` tool to convert the IDL file to JSON and HTML files (or use the hosted translator -- see below)
* Install the language binding for the lanuage you're writing the server in 
  (See: http://barrister.bitmechanic.com/download.html)
* Write a server that implements the interfaces in the IDL

This project contains the core `barrister` command line tool as well as the Python bindings.

## Installation

### Hosted Translator

If you are working in a language other than Python and don't wish to install the barrister Python
package, you can use the hosted translator to convert your IDL to its JSON representation.  For example:

    curl --data-urlencode idl@foo.idl http://barrister.bitmechanic.com/run > foo.json

This would upload `foo.idl` and save the output as `foo.json`.  Currently the hosted error output is fairly
minimal, but if you get valid JSON back on the response then you should be set.

### Install

I suggest installing pip.  All Python distributions that I'm aware of ship with `easy_install`, so if 
you don't have `pip` yet, you can try:

    easy_install pip
    
Then you simply run:

    pip install barrister
    
You may need to be root to install packages globally, in which case you should `su` to root or 
use `sudo`:

    sudo pip install barrister

### Dependencies

If you're using Python 2.6 or later, you're good to go.  Python 2.5 users will need to:

    pip install simplejson
    
Python 2.3 and 2.4 users will need to:

    pip install uuid simplejson
    
### Graphviz diagrams

As of 0.1.3 barrister can optionally generate UML-ish diagrams using Graphviz.
To generate a diagram, use the `-p` and optionally `-z` flags to barrister.

The Graphviz `dot` program must be installed and in your PATH.  See the
[Graphviz site](http://www.graphviz.org/) for installation details.  Most Linux distros can install
Graphviz via a package manager (apt, yum, pacman, etc).  Mac users can install
Graphviz with [homebrew](http://mxcl.github.com/homebrew/).

If you'd like the diagram embedded in the generated HTML doc, place the token:
`[[diagram]]` in your IDL file where you'd like the diagram to appear.  This
string will be replaced with a HTML `<img>` tag pointing to the diagram.

## Documentation

* Read the [Contact Service Tutorial](https://github.com/coopernurse/barrister-demo-contact/tree/master/python)
* Read the [IDL Docs](http://barrister.bitmechanic.com/docs.html) for more info on writing 
  Barrister IDL files
* View the [API Reference](http://barrister.bitmechanic.com/api/python/latest/) based on the 
  latest commit to master

## License

Distributed under the MIT license.  See LICENSE file for details.

## Release / Tag notes

Note to self on how to tag release

    # Edit `setup.py` and `__init__.py`, bump version, then run:
    
    git add -u
    git commit -m "bump v0.1.0"
    git tag -a v0.1.0 -m "version 0.1.0"
    git push --tags
    git push
    python setup.py sdist upload
    
