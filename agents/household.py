"""
Class for household agents.
"""

import shared

HIDGen = shared.IDGenerator()

class Household(object):
    "Represents a single household agent"
    def __init__(self):
        self._HID = HIDGen.next()
        self._anyNonWoodFuel = shared.Boolean()
        self._OwnHousePlot = shared.Boolean()
        self._OwnLand = shared.Boolean()
        self._RentedOutLand = shared.Boolean()
        self._members = set()

    def get_HID(self):
        "Returns the ID of this household"
        return self._HID

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
