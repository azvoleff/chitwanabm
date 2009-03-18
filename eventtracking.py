"""
Part of Chitwan Valley agent-based model.

Classes for life events such as marriage, birth, migration, etc. Allows easier 
tracking of these events when plotting results.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

class Event(dict):
    def

class Results(object):
    def __init__(self, start_time):
        self._time = [start_time]
        self._censues= {}
        self._births = {}
        self._deaths = {}
        self._marriages = {}
        self._migrations = {}

    def increment_time(self):
        self.

    def add_births(self, births):
        if len(self._births) == (len(self._time) - 1)
            self._births.append(births)
        else:
            raise Error("model results already stored for this timestep")
