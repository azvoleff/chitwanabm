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
# Contact Alex Zvoleff (azvoleff@mail.sdsu.edu) in the Department of Geography 
# at San Diego State University with any comments or questions. See the 
# README.txt file for contact information.

"""
Script to run a test of the Chitwan Valley ABM code, to ensure, for example, 
that agents are properly initialized, and that demographic processes 
(marriages, deaths, births, migrations) are all properly represented in the 
model.
"""

import sys
import logging

logger = logging.getLogger(__name__)

import numpy as np

from matplotlib import pyplot as plt

def main(argv=None):
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    log_console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
            datefmt='%I:%M:%S%p')
    ch.setFormatter(log_console_formatter)
    logger.addHandler(ch)

    sample_size = 10000
    
    logger.info("Plotting desired number of children test histogram")
    from ChitwanABM.statistics import calc_des_num_children
    retvalues = []
    for n in xrange(sample_size):
        retvalues.append(calc_des_num_children())
    print retvalues[1:100]
    plt.hist(retvalues, bins=(-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
    plt.title("Desired Number of Children")
    plt.show()

    logger.info("Plotting birth interval test histogram")
    from ChitwanABM.statistics import calc_birth_interval
    retvalues = []
    for n in xrange(sample_size):
        retvalues.append(calc_birth_interval())
    print retvalues[1:100]
    plt.hist(retvalues)
    plt.title("Birth interval")
    plt.show()

    logger.info("Plotting household area test histogram")
    from ChitwanABM.statistics import calc_hh_area
    retvalues = []
    for n in xrange(sample_size):
        retvalues.append(calc_hh_area())
    print retvalues[1:100]
    plt.hist(retvalues, bins=(30, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000))
    plt.title("Household Plot Land Area (sq. m)")
    plt.show()

    logger.info("Plotting num in migrant households test histogram")
    from ChitwanABM.statistics import calc_num_inmigrant_households
    retvalues = []
    for n in xrange(sample_size):
        retvalues.append(calc_num_inmigrant_households())
    print retvalues[1:100]
    plt.hist(retvalues, bins=(0, 5, 10, 15, 20, 25, 30))
    plt.title("Number of In-migrant Households")
    plt.show()

    logger.info("Plotting in migrant household ethnicity test histogram")
    from ChitwanABM.statistics import calc_inmigrant_household_ethnicity
    retvalues = []
    for n in xrange(sample_size):
        retvalues.append(calc_inmigrant_household_ethnicity(as_integer=True))
    print retvalues[1:100]
    plt.hist(retvalues)
    plt.title("In-migrant Household Ethnicity")
    plt.show()

    logger.info("Plotting in migrant household size test histogram")
    from ChitwanABM.statistics import calc_inmigrant_household_size
    retvalues = []
    for n in xrange(sample_size):
        retvalues.append(calc_inmigrant_household_size())
    print retvalues[1:100]
    plt.hist(retvalues)
    plt.title("In-migrant Household Size")
    plt.show()

def validate_person_attributes(world):
    def get_person_info(person):
        if person.is_away():
            household_ID = None
            neighborhood_ID = None
        else:
            household_ID = person.get_parent_agent().get_ID()
            neighborhood_ID = person.get_parent_agent().get_parent_agent().get_ID()
        person_info = "(age: %.2f, ethnicity: %s, in-mig: %s, initial: %s, HH: %s, NBH: %s, in %s store(s), alive: %s)"%(
                person.get_age_years(), person.get_ethnicity(), 
                person.is_in_migrant(), person.is_initial_agent(), 
                household_ID, neighborhood_ID,
                len(person._store_list), person._alive)
        return person_info
    logger.debug("Validating person attributes")
    all_agents_valid = True
    valid_ethnicities = ["HighHindu",
                         "HillTibeto",
                         "LowHindu",
                         "Newar",
                         "TeraiTibeto"]
    maximum_age = 115
    checked_person_list = []
    spouse_count_dict = {}
    for person in world.iter_all_persons():
        person_info = get_person_info(person)
        if person.get_parent_agent() == None and not person.is_away():
            logger.warning("Person %s is not a member of any household %s"%(
                person.get_ID(), person_info))
            all_agents_valid = False
        if person.get_spouse() != None and spouse_count_dict.has_key(person.get_spouse().get_ID()):
            spouse_count_dict[person.get_spouse().get_ID()] += 1
            logger.warning("Person %s has %s spouses"%(person.get_ID(), spouse_count_dict[person.get_spouse().get_ID()]))
            all_agents_valid = False
        elif person.get_spouse() != None and not spouse_count_dict.has_key(person.get_spouse().get_ID()):
            spouse_count_dict[person.get_spouse().get_ID()] = 1
        if person in checked_person_list:
            logger.warning("Person %s is a member of more than one household"%(
                person.get_ID(), person_info))
            all_agents_valid = False
        if person.get_age_months() != np.round(person.get_age_years() * 12):
            logger.warning("Person %s age in months (%.2f) does not match age in years (%.2f) %s"%(
                person.get_ID(), person.get_age_months(), person.get_age_years(), person_info))
            all_agents_valid = False
        if person.get_age_years() > maximum_age:
            logger.warning("Person %s is older than the maximum allowed age (%s) %s"%(
                person.get_ID(), maximum_age, person_info))
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
        if person.get_spouse() != None and person._marriage_time <= 1920:
            spouse_info = get_person_info(person.get_spouse())
            logger.warning("Person %s (spouse ID %s) was married in %.2f. Person: %s, Spouse: %s"%(
                person.get_ID(), person.get_spouse().get_ID(), person._marriage_time,  person_info, spouse_info))
            all_agents_valid = False
        if person._des_num_children > 10:
            logger.warning("Desired number of children for person %s is %s"%(person.get_ID(), person._des_num_children))
            all_agents_valid = False
    return all_agents_valid

def validate_household_attributes(world):
    logger.debug("Validating household attributes")
    # TODO: Complete validation function.
    all_agents_valid = True
    for region in world.iter_regions():
        for household in region.iter_households():
            if household.get_agents() == [] and household.get_away_members() == []:
                logger.warning("Household %s has no members."%household.get_ID())
                all_agents_valid = False
            if household.get_parent_agent() == None:
                logger.warning("Household %s is not a member of any neighborhood."%household.get_ID())
                all_agents_valid = False
    return all_agents_valid

def validate_neighborhood_attributes(world):
    logger.debug("Validating neighborhood attributes")
    # TODO: Complete validation function.
    all_agents_valid = True
    for region in world.iter_regions():
        for neighborhood in region.iter_agents():
            if neighborhood.get_agents() == []:
                logger.warning("Neighborhood %s has no members."%neighborhood.get_ID())
                all_agents_valid = False
            if neighborhood._land_agveg < 0 or neighborhood._land_nonagveg < 0 or neighborhood._land_privbldg < 0 or neighborhood._land_pubbldg < 0 or neighborhood._land_other < 0:
                logger.warning("Neighborhood %s has a land use class with < 0 area: %.2f, %.2f, %.2f, %.2f, %.2f"%(
                    neighborhood.get_ID(), neighborhood._land_agveg,
                    neighborhood._land_nonagveg, neighborhood._land_privbldg, 
                    neighborhood._land_pubbldg, neighborhood._land_other))
                all_agents_valid = False
    return all_agents_valid

if __name__ == "__main__":
    sys.exit(main())
