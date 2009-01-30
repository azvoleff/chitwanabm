"""
Part of Chitwan Valley agent-based model.

Class for person agents.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

from chitwanABM import 

PIDGen = IDGenerator()

class Population(object):
    "Represents a set of persons sharing certain demographic characteristics."
    def __init__(self):
        self._persons = {}

    def getCouple(self):
        # couples will start out as a list of one spouse from each couple, then 
        # be extended to become a list of couples
        couples = []
        for person in self._persons():
            if person.is_married() and person.getSpousePID:
                # store the first spouse
                couples.append(person)

        # Now store the second spouse
        #for couple in self.couples():
        #    couple.extend(self._persons[couple.

class Person(object):
    "Represents a single person agent"
    def __init__(self, birthday, age=None):
        # birthday is the timestep of the birth of the agent. It is used to 
        # calculate the age of the agent. birthdays can be negative for those 
        # agents used to initialize the model, to represent agents who existed 
        # prior to time 0
        self._birthDate = birthday

        self._PID = PIDGen.next()
        self._sex = None #TODO

    def get_PID(self):
        return self._PID

    def get_spouse_PID(self):
        try:
            return self._spousePID
        except AttributeError:
            raise AttributeError("spouse of agent %i is not defined"%self.get_PID())

    def marry(self, spouse):
        "Marries this agent to another Person instance."
        self._spousePID = spouse.GetPID()
        other._spousePID = self.GetPID()

    def is_married(self):
        "Returns a boolean indicating if person is married or not."
        if self._spousePID == None:
            return False
        else:
            return True

    def survival(self):
        "Determines whether Person will survive the timestep."
        # TODO: when called, this function will take into account 
        # age/sex/whatever else to determine whether the person agent survives 
        # or dies during this time step

    def kill_agent(self):
        "Kills an agent, and fixes the relationships of spouses, households, etc."
        # TODO: this function will "kill" the agent, most likely as a result of 
        # the outcome of the Survival function. Will need to deal with children 
        # and spouse PIDs

#class Ancestors(list):
    "Stores a list of person agents for later recall and analysis"
    # TODO: This class will contain a list of deceased person agents, mostly for 
    # debugging the model, although the results could also be used for plotting 
    # purposes.
    #def AddPerson(self, person):
