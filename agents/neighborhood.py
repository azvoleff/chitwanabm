"""
Part of Chitwan Valley agent-based model.

Class for neighborhood agents.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

from chitwanABM import rcParams
from chitwanABM.agents import IDGenerator, boolean_choice

NIDGen = IDGenerator()

class Neighborhood(object):
    "Represents a single neighborhood agent"
    def __init__(self):
        self._NID = NIDGen.next()
        self._NumYearsNonFamilyServices = 15 #TODO
        self._ElecAvailable = boolean_choice()
        self._members = set()

    def get_NID(self):
        "Returns the ID of this neighborhood."
        return self._NID

    def add_household(self, household):
        "Adds a new household to the neighborhood."

    def remove_household():
        "Removes a household from the neighborhood."

    def years_non_family_services(self):
        "Number of years non-family services have been available."
        return self._NumYearsNonFamilyServices

    def elec_available(self):
        "Boolean for whether neighborhood has electricity."
        return self._ElecAvailable
