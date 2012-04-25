# Barrister

Barrister lets you write well documented services that can be consumed from a variety of languages.  
The basic steps are:

* Write an IDL file (See: http://barrister.bitmechanic.com/docs.html)
* Run the `barrister` tool to convert the IDL file to JSON and HTML files
* Install the language binding for the lanuage you're writing the server in 
  (See: http://barrister.bitmechanic.com/download.html)
* Write a server that implements the interfaces in the IDL

This project contains the core `barrister` command line tool as well as the Python bindings.

## Installation

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

    # Edit `setup.py`, bump version, then run:
    
    git add -u
    git commit -m "bump v0.1.0"
    git tag -a v0.1.0 -m "version 0.1.0"
    git push --tags
    git push
    python setup.py sdist upload
    
