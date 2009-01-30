"""
The classes in this module define the agent types used in the Chitwan Valley 
model. Land use is also represented by a 'landuse' class.

    person.py - Defines the person agent class, as well as a 'population' class 
                to represent a set of agents.
    household.py - Defines the household agent class.
    neighborhood.py - Defines the neighborhood agent class.
    landuse.py - Defines the landuse class.

Included here are functions shared by the agent classes.
"""

import numpy as np

class IDGenerator(object):
    "A generator class for consecutive unique ID numbers."
    def __init__(self):
        # Start at -1 so the first ID will be 0
        self._PID = -1

    def next(self):
        self._PID += 1
        return self._PID

def boolean_choice(trueProb=.5):
    if np.random.rand() < trueProb:
        return True
    else:
        return False
