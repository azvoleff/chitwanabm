from __future__ import with_statement
from fabric.api import local, settings, abort, run, cd, env, put, task

python = "C:/Python27/python.exe"
python64 = "C:/Python27_64bit/python.exe"
sphinx_build = "C:/Python27/Scripts/sphinx-build.exe"
sphinx_build64 = "C:/Python27_64bit/Scripts/sphinx-build.exe"

import os

@task
def generate_docs():
    local("%s -b dirhtml -d doc\_build\doctrees doc doc\_build\html"%sphinx_build64)
    #local("%s -b pdf -d doc\_build\doctrees doc doc\_build\pdf"%sphinx_build)

@task
def upload_to_pypi():
    local("%s setup.py register sdist bdist_egg bdist_wininst upload"%python)
    local("%s setup.py register sdist bdist_egg bdist_wininst upload"%python64)
