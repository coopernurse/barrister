# Barrister

Barrister lets you write well documented services that can be consumed from a variety of languages.  The
basic steps are:

* Write an IDL file (See: http://barrister.bitmechanic.com/docs.html)
* Run the `barrister` tool to convert the IDL file to JSON and HTML files
* Install the language binding for the lanuage you're writing the server in 
  (See: http://barrister.bitmechanic.com/download.html)
* Write a server that implements the interfaces in the IDL

This project contains the core `barrister` command line tool as well as the Python bindings.

## Installation

I suggest installing pip.  All Python distributions that I'm aware of ship with `easy_install`, so if 
you don't have `pip` yet, you can try:

    easy_install pip
    
Then you simply run:

    pip install barrister
    
You may need to be root to install packages globally, in which case you should `su` to root or use `sudo`:

    sudo pip install barrister
    
## Writing an IDL file

The [main Barrister docs](http://barrister.bitmechanic.com/docs.html) explain how to write an IDL file and
run the `barrister` tool to convert it to a `json` file.

## Writing a Server

## Writing a Client

### Example

### Batch Calls



