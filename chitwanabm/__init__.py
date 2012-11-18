# Copyright 2008-2012 Alex Zvoleff
#
# This file is part of the chitwanabm agent-based model.
# 
# chitwanabm is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# chitwanabm is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# chitwanabm.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff (azvoleff@mail.sdsu.edu) in the Department of Geography 
# at San Diego State University with any comments or questions. See the 
# README.txt file for contact information.
"""
'chitwanabm' is an agent-based model of the Western Chitwan Valley, Nepal. The 
model represents a subset of the population of the Valley using a number of 
agent types (person, household and neighborhood agents), environmental 
variables (topography, land use and land cover) and social context variables.

Construction of the model is supported as part of an ongoing National Science 
Foundation Partnerships for International Research and Education (NSF PIRE) 
project (grant OISE 0729709) investigating human-environment interactions in 
the Western Chitwan Valley.
"""

__version__ = '1.4.2dev'

from pyabm import rc_params, np
# Set rcparams._initialized to False as rcparams still need to be initialized 
# with the chitwanabm specific params - they have only been initialized for 
# pyabm at this point.
rc_params._initialized = False
