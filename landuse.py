# Copyright 2009 Alex Zvoleff
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

Land use class: Tracks land use and land use change.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

class LandUse():
    def __init__(self):
        'Initializes a land use type object.'
        self._time = []
        self._proportions = []
        # 'coeffs' is a vector of OLS regression coefficients
        # TODO: define this coeff matrix
        self._coeffs = []

    def add_value(self, time, proportion):
        'Adds a new landuse value in manually (without OLS)'
        self._time.append(time)
        self._proportions(proportion)

    def get_value(self, time):
        'Retrieves landuse at a given time'
        index = self._time.index(time)
        return self._proportions(index)

    def calc_value(self, time, predictors):
       'Calculates landuse at time t using OLS, from a vector of predictors' 
       self._time.append(time)
       self._proportions.append(dot(predictors, self._coeffs)) #TODO: Is this right?
