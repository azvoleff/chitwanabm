# Copyright 2008-2012 Alex Zvoleff
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
Part of Chitwan Valley agent-based model.

Sets up rc parameters so that they can be loaded and reused by other parts of 
the model.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import os
import sys
import warnings

import numpy as np

# This is the rcParams instance that will be used to setup all of the 
# parameters for this model. The random_state instance will be used for all 
# random number generation, to ensure that the random seed is stored and known 
# for future replication of the results.
from PyABM import rcParams, random_state
