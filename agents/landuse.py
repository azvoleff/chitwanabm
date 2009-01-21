#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

Land use class: Tracks land use and land use change.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

class LandUse():
    def __init__(self, coeff):
        'Initializes a land use type object.'
        self._time = []
        self._proportion = []
        # 'coeffs' is a vector of OLS regression coefficients
        self._coeffs = coeff

    def addValue(self, time, proportion):
        'Adds a new landuse value in manually (without OLS)'
        self._time.append(time)
        self._proportion(proportion)

    def getValue(self, time):
        'Retrieves landuse at a given time'
        index = self._time.index(time)
        return self._proportion(index)

    def calcValue(self, time, predictors):
       'Calculates landuse at time t using OLS, from a vector of predictors' 
       self._time.append(time)
       self._proportion.append(dot(predictors, self._coeffs)) #TODO: Is this right?
