"""
Part of Chitwan Valley agent-based model.

Class for person agents.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

from chitwanABM import rcParams
from chitwanABM.agents import IDGenerator, boolean_choice

PIDGen = IDGenerator()

class Region(object):
    "Represents a set of neighborhoods sharing certain demographic characteristics."
    def __init__(self):
        # This will store a dictionary of all persons in the population, keyed 
        # by PID
        self._neighborhoods = {}

        # Now setup the demographic variables for this population, based on the 
        # values given in the model rc file
        self._hazard_birth = rcParams['hazard_birth']
        self._hazard_death = rcParams['hazard_death']
        self._hazard_marriage = rcParams['hazard_marriage']

    def births(self, time):
        """Runs through the population and agents give birth probabilistically 
        based on their sex, age and the hazard_birth for this population"""
        # TODO: This should take account of the last time the agent gave birth 
        # and adjust the hazard accordingly
        for neighborhood in self._neighborhoods:
            for household in neighborhood.get_households():
                for person in household.get_persons():
                    if (person.get_sex() == 'female') and (np.random.random()
                            < self._hazard_birth[person.get_age()]):
                                # Agent gives birth. First find the father 
                                # (assumed to be the spouse of the person 
                                # giving birth).
                                dad = household.get_person(person.get_spousePID())
                                # Now have the mother give birth, and add the 
                                # new person to the mother's household.
                                household.add_person(person.give_birth(time, father=dad))
                        
    def deaths(self, time):
        """Runs through the population and kills agents probabilistically based 
        on their age and the hazard_death for this population"""
        for neighborhood in self._neighborhoods:
            for household in neighborhood.get_households():
                for person in household.get_persons():
                    if (person.get_sex() == 'female') and (np.random.random()
                            < self._hazard_death[person.get_age()]):
                                # Agent dies:
                                person.kill()
                                household.remove_person(person.give_birth(time))
                        
    def marriages(self, time):
        """Runs through the population and marries agents probabilistically 
        based on their age and the hazard_marriage for this population"""
        for neighborhood in self._neighborhoods:
            for household in neighborhood.get_households():
                for person in household.get_persons():
                    if (person.get_sex() == 'female') and (np.random.random()
                            < self._hazard_marriage[person.get_age()]):
                                # Agent gets married:
                                person.marry(person.get_PID())
                        
    def increment_age(self):
        """Adds one to the age of each agent. The units of age are dependent on 
        the units of the input rc parameters."""
        for neighborhood in self._neighborhoods:
            for household in neighborhood.get_households():
                for person in household.get_persons():
                    person._age += 1

    def kill_agent(self):
        "Kills an agent, removing it from its household, and its marriage."

    def census(self):
        "Returns the number of persons in the population."
        total = 0
        for neighborhood in self._neighborhoods:
            for household in neighborhood.get_households():
                total += household.num_members()
        return total

class Person(object):
    "Represents a single person agent"
    def __init__(self, birthdate, mother=None, father=None, age=0, initial_agent=False):
        # birthdate is the timestep of the birth of the agent. It is used to 
        # calculate the age of the agent. Agents have a birthdate of 0 if they 
        # were BORN in the first timestep of the model.  If they were used to 
        # initialize the model their birthdates will be negative.
        self._birthdate = birthdate
        # deathdate is used for tracking agent deaths in the results, mainly 
        # for debugging.
        self._deathdate = None

        # self._initial_agent is set to "True" for agents that were used to 
        # initialize the model.
        self._initial_agent = initial_agent

        # self._age is used as a convenience to avoid the need to calculate the 
        # agent's age from self._birthdate each time it is needed. It is 
        # important to remember though that all agent's ages must be incremented 
        # with each model timestep. The age starts at 0 (it is zero for the 
        # entire first timestep of the model).
        self._age = age

        # self._PID is unique ID number used to track each person agent.
        self._PID = PIDGen.next()

        # Also need to store information on the agent's parents. For agents used 
        # to initialize the model both parent fields are set to "None"
        if father == None:
            self._father_PID = None
        else:
            self._father_PID = father.get_PID()

        if mother == None:
            self._mother_PID = None
        else:
            self._mother_PID = mother.get_PID()

        # Person agents are randomly assigned a sex
        if boolean_choice(.5):
            self._sex = 'female'
        else:
            self._sex = 'male'

        self._spousePID = None

    def get_PID(self):
        return self._PID

    def get_sex(self):
        return self._sex

    def get_spouse_PID(self):
        return self._spousePID

    def marry(self, other):
        "Marries this agent to another Person instance."
        self._spousePID = other.get_PID()
        other._spousePID = self.get_PID()

    def give_birth(self, time, dad):
        "Agent gives birth. New agent inherits characterists of parents."
        assert self.get_sex() == 'female', "Men can't give birth"
        assert self.get_PID() != dad.get_PID(), "No immaculate conception"
        assert self.get_spouse_PID() == dad.get_PID(), "In Chitwan, all births are in marriages"
        baby = Person(birthdate=time, mother=self, father=dad)
        return baby

    def is_married(self):
        "Returns a boolean indicating if person is married or not."
        if self._spousePID == None:
            return False
        else:
            return True
