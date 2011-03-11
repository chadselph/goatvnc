#!/usr/bin/env python

from distutils.core import setup

setup(name='goatvnc',
    version='.0.2',
    description='Twisted Python VNC Server',
    author='Chad Selph',
    packages=['goatvnc'],
    requires=['PIL','Twisted'],
    package_dir={'goatvnc':'src/'},
)

