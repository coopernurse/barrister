"""
Barrister
---------

Polyglot RPC system that can enforce types expressed in an easy to write IDL.
Designed to be enjoyable to use from both static and dynamic languages.

Links
`````

* `main site <http://barrister.bitmechanic.com/>`_
* `GitHub repo <https://github.com/coopernurse/barrister>`_

"""
from distutils.core import setup

setup(
    name='barrister',
    version='0.1.1b',
    url='https://github.com/coopernurse/barrister',
    scripts=['bin/barrister'],
    packages=['barrister',],
    license='MIT',
    author='James Cooper',
    author_email='james@bitmechanic.com',
    description='Polyglot RPC',
    long_description=__doc__,
    install_requires=[
        'Markdown',
        'plex'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: System :: Distributed Computing',
        'Topic :: Software Development :: Libraries'
    ]
)
