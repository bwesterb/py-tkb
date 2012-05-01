#!/usr/bin/env python

from setuptools import setup, find_packages
from get_git_version import get_git_version
import os, os.path

def find_package_data():
    base = os.path.join(os.path.dirname(__file__), 'src')
    s, r = ['.'], []
    while s:
        p = s.pop()
        for c in os.listdir(os.path.join(base, p)):
            if os.path.isdir(os.path.join(base, p, c)):
                s.append(os.path.join(p, c))
            elif c.endswith('.mirte'):
                r.append(os.path.join(p, c))
    return r

setup(name='py-tkb',
      version=get_git_version(),
      description='Client for tkbd daemon',
      author='Bas Westerbaan',
      author_email='bas@westerbaan.name',
      url='http://github.com/bwesterb/py-tkb/',
      packages=['tkb'],
      package_dir={'tkb': 'src'},
      package_data={'tkb': find_package_data()},
      install_requires = ['mirte>=0.1.5',
                          'py-joyce>=0.1.8'],
      entry_points = {
          'console_scripts': [
              'tkb = tkb.main:main',
              ]
          }
      )

# vim: et:sta:bs=2:sw=4:
