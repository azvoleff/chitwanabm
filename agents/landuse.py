#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

landuse.py - Class for land use.
Tracks land use and land use change.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

class LandUse():
    def __init__(self):
        self._time = []
        self._proportion = []

    def addValue(self, time, proportion):
        self._time.append(time)
        self._proportion(proportion)

    def calcValue(self, time):
        index = self._time.index(time)
        return self._proportion(index)
