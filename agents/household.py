"""
Part of Chitwan Valley agent-based model.

Class for household agents.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

from chitwanABM import rcParams
from chitwanABM.agents import IDGenerator, boolean_choice

HIDGen = IDGenerator()

class Household(object):
    "Represents a single household agent"
    def __init__(self):
        self._HID = HIDGen.next()
        self._anyNonWoodFuel = boolean_choice()
        self._OwnHousePlot = boolean_choice()
        self._OwnLand = boolean_choice()
        self._RentedOutLand = boolean_choice()

        # _members stores household members in a dictionary keyed by PID
        self._members = {}

    def get_HID(self):
        "Returns the ID of this household"
        return self._HID

    def add_person(self, person):
        "Adds a new person to the household, either from birth or marriage"
        if self._members.has_key(person.get_PID()):
            raise KeyError("person %s is already a member of household %s"%(person.get_PID(), self._HID))
        self._members[person.get_PID()] = person

    def remove_person(self, person):
        """Removes a person from household, either from death, migration, or 
        marriage to a member of another household."""
        try:
            self._members.pop(person.get_PID())
        except KeyError:
            raise KeyError("person %s is not a member of household %s"%(person.get_PID(), self._HID))

    def num_members(self):
        return len(self._members)

    def any_non_wood_fuel(self):
        "Boolean for whether household uses any non-wood fuel"
        return self._anyNonWoodFuel

    def own_house_plot(self):
        "Boolean for whether household owns the plot of land on which it resides"
        return self._OwnHousePlot

    def own_any_land(self):
        "Boolean for whether household owns any land"
        return self._OwnLand

    def rented_out_land(self):
        "Boolean for whether household rented out any of its land"
        return self._RentedOutLand
