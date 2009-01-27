#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

Contains classes/functions shared among the different agent classes.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

class IDGenerator(object):
    "A generator class for consecutive unique ID numbers."
    def __init__(self):
        self._PID = -1

    def next(self):
        self._PID += 1
        return self._PID

def Boolean(trueProb=.5):
    if np.random.rand() < trueProb:
        return True
    else:
        return False
