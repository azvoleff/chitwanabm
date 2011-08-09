#!/usr/bin/env python
# Copyright 2011 Alex Zvoleff
#
# This file is part of the ChitwanABM agent-based model.
# 
# ChitwanABM is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# ChitwanABM is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# ChitwanABM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff in the Department of Geography at San Diego State 
# University with any comments or questions. See the README.txt file for 
# contact information.

"""
Installs the Python dependencies and R packages required to run the ChitwanABM 
model.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import os
import sys
import subprocess

from ChitwanABM import rcParams

def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        rc_file = sys.argv[1]
        print "\nWARNING: using default rc params. Custom rc_file use is not yet implemented.\n"
    except IndexError:
        pass

    Rscript_binary = rcParams['path.Rscript_binary']
    dev_null = open(os.devnull, 'w')
    subprocess.check_call([Rscript_binary, 'plot_pop.R', results_path],
            cwd=sys.path[0], stdout=dev_null, stderr=dev_null)
