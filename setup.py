#!/usr/bin/python

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "chitwanabm",
    version = "1.5dev",
    packages = ['chitwanabm'],
    package_dir = {'chitwanabm' : 'chitwanabm'},
    package_data = {'chitwanabm' : ['rcparams.default',
                                    'chitwanabmrc.windows',
                                    'R/*.R']},
    zip_safe = True,
    install_requires = ['numpy >= 1.6.1',
                        'matplotlib >= 0.98.4',
                        'pyabm >= 0.3'],
    author = "Alex Zvoleff",
    author_email = "azvoleff@mail.sdsu.edu",
    description = "An agent-based model of the Chitwan Valley, Nepal",
    keywords = "agent-based modeling ABM simulation model",
    license = "GPL v3 or later",
    url = "http://rohan.sdsu.edu/~zvoleff/research/chitwanabm",   # project home page, if any
    long_description = ''.join(open('README.rst').readlines()[6:]),
    classifiers = [
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Life",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7"]
)
