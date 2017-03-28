#!/usr/bin/env python

from distutils.core import setup

setup(name='telcal_utils',
      version='0.0',
      description='Code for parsing/plotting VLA TelCal output',
      author='Paul Demorest',
      author_email='pdemores@nrao.edu',
      url='http://github.com/demorest/telcal_utils',
      py_modules=['telcal'],
      scripts=['telcal_gui.py']
     )
