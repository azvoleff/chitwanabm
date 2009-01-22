#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

Class for household agents.

Alex Zvoleff, azvoleff@mail.sdsu.edu
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

    def GetHID(self):
        "Returns the ID of this household."
        return self._HID

    def AnyNonWoodFuel(self):
        "Boolean for whether household uses any non-wood fuel"
        return self._anyNonWoodFuel

    def OwnHousePlot(self):
        "Boolean for whether household owns the plot of land on which it resides"
        return self._OwnHousePlot

    def OwnAnyLand(self):
        "Boolean for whether household owns any land"
        return self._OwnLand

    def RentedOutLand(self):
        "Boolean for whether household rented out any of its land"
        return self._RentedOutLand
