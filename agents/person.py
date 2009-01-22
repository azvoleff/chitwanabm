#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

Class for person agents.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""
class PIDGenerator():
    def __init__()
    i = 0
    i += 1
    yield i

class Person():
    def __init__(self, birthday):
        self._birthDate = birthday
        self._age = None #TODO
        self._sex = None #TODO
        self._PID = PIDGenerator()
        self._spousePID = None

    def Marry(self, spouse):
        "Marries this agent to another Person instance."
        self._spousePID = spouse.GetPID()
        other._spousePID = self.GetPID()

    def IsMarried(self):
        "Returns a boolean indicating if person is married or not."
        if self._spousePID == None:
            return False
        else:
            return True

    def Survival(self):
        "Determines whether Person will survive the timestep."
        # TODO: when called, this function will take into account 
        # age/sex/whatever else to determine whether the person agent survives 
        # or dies during this time step

    def KillAgent(self):
        "Kills an agent, and fixes the relationships of spouses, households, etc."
        # TODO: this function will "kill" the agent, most likely as a result of 
        # the outcome of the Survival function. Will need to deal with children 
        # and spouse PIDs

#class Ancestors(list):
    "Stores a list of person agents for later recall and analysis"
    #def AddPerson(self, person):

    # TODO: This class will contain a list of deceased person agents, mostly for 
    # debugging the model, although the results could also be used for plotting 
    # purposes.
