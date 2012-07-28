#!/usr/bin/python
# Copyright 2008-2012 Alex Zvoleff
#
# This file is part of the ChitwanABM agent-based model.
# 
# ChitwanABM is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# ChitwanABM is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# ChitwanABM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff in the Department of Geography at San Diego State 
# University with any comments or questions. See the README.txt file for 
# contact information.

"""
Part of Chitwan Valley agent-based model.

Script to run a test of the Chitwan Valley ABM code, to ensure, for example, 
that agents are properly initialized, and that demographic processes 
(marriages, deaths, births, migrations) are all properly represented in the 
model.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import logging

logger = logging.getLogger(__name__)

import numpy as np

def validate_person_attributes(world):
    def get_person_info(person):
        person_info ="(age: %.2f, ethnicity: %s, in-mig: %s, initial: %s, HH: %s, NBH: %s, stores: %s, alive: %s)"%( \
                person.get_age_years(), person.get_ethnicity(), 
                person.is_in_migrant(), person.is_initial_agent(), 
                person.get_parent_agent().get_ID(),
                person.get_parent_agent().get_parent_agent().get_ID(), 
                person._store_list, person._alive)
        return person_info
    logger.debug("Validating person attributes")
    all_agents_valid = True
    valid_ethnicities = ["HighHindu",
                         "HillTibeto",
                         "LowHindu",
                         "Newar",
                         "TeraiTibeto"]
    maximum_age = 110
    for person in world.iter_persons():
        if person.get_parent_agent() == None:
            logger.warning("Person %s %s is not a member of any household"%(
                person.get_ID(), person_info))
            all_agents_valid = False
        person_info = get_person_info(person)
        if person.get_age_months() != np.round(person.get_age_years() * 12):
            logger.warning("Person %s age in months (%.2f) does not match age in years (%.2f) %s"%(
                person.get_ID(), person.get_age_months(), person.get_age_years(), person_info))
            all_agents_valid = False
        if person.get_age_years() > maximum_age:
            logger.warning("Person %s is older than the maximum allowed age (%s) %s"%(
                person.get_ID(), maximum_age, person.get_age_years(), person_info))
            all_agents_valid = False
        if person.get_ethnicity() not in valid_ethnicities:
            logger.warning("Person %s is not a valid ethnicity %s"%(person.get_ID(), person_info))
            all_agents_valid = False
        if not person._alive:
            logger.warning("Person %s %s is dead, but is still participating in household activities"%(
                person.get_ID(), person_info))
            all_agents_valid = False
        if person.get_age_years() < 0 or person.get_age_months() < 0:
            logger.warning("Person %s %s has not been born yet, but is already participating in household activities"%(
                person.get_ID(), person_info))
            all_agents_valid = False
        if person.get_spouse() != None and not person.get_spouse()._alive:
            spouse_info = get_person_info(person.get_spouse())
            logger.warning("Spouse of person %s (spouse ID %s) is dead. Person: %s, Spouse: %s"%(
                person.get_ID(), person.get_spouse().get_ID(), person_info, spouse_info))
            all_agents_valid = False
    return all_agents_valid

def validate_household_attributes(world):
    logger.debug("Validating household attributes")
    # TODO: Complete validation function.
    all_agents_valid = True
    for region in world.iter_regions():
        for household in region.iter_households():
            pass
    return all_agents_valid

def validate_neighborhood_attributes(world):
    logger.debug("Validating neighborhood attributes")
    for region in world.iter_regions():
        for neighborhood in region.iter_agents():
            pass
    # TODO: Complete validation function.
    all_agents_valid = True
    return all_agents_valid
