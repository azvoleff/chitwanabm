#!/usr/bin/env python
# Copyright 2009 Alex Zvoleff
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
Sets up a ChitwanABM model run: Initializes neighborhood/household/person agents 
and land use using the original CVFS data.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import sys

import numpy as np
import pickle
from subprocess import check_call, CalledProcessError

from ChitwanABM import rcParams
from ChitwanABM.agents import World

def main():
    generate_world()

def read_CVFS_data(textfile, key_field):
    """
    Reads in CVFS data from a CSV file into a dictionary of dictionary objects, 
    where the first line of the file gives the column headings (used as keys 
    within the nested dictionary object). No conversion of the fields is done: 
    they are all stored as strings, EXCEPT for the key_field, which is 
    converted and stored as an int.
    """

    try:
        file = open(textfile, 'r')
        lines = file.readlines()
        file.close()
    except:
        raise IOError("error reading %s"%(textfile))
    
    # The first line of the data file gives the column names
    col_names = lines[0].split(',')
    for n in xrange(len(col_names)):
        col_names[n] = col_names[n].strip('\n \"')

    data = {}
    for line in lines[1:]:
        fields = line.split(',')
        for n in xrange(len(fields)):
            fields[n] = fields[n].strip('\n \"')

        new_data = {} 
        for field, column_name in zip(fields, col_names):
            new_data[column_name] = field

        data_key = int(new_data[key_field])
        if new_data.has_key(data_key):
            raise KeyError('key %s is already in use'%(data_key))
        data[data_key] = new_data

    return data

def assemble_neighborhoods(neighborhoodsFile, neighborhoods_coords_file, model_world):
    """
    Reads in data from the CVFS (from dataset DS0014) on number of years 
    non-family services were available within a 30 min walk of each 
    neighborhood (SCHLFT, HLTHFT, BUSFT, MARFT, EMPFT) and on whether 
    neighborhood was electrified (ELEC).
    """
    neigh_datas = read_CVFS_data(neighborhoodsFile, "NEIGHID") 
    # Can't use the CVFS coordinate data as it is in UTM45N, while all the 
    # other data is in UTM44N. So use this separate CSV file to read 
    # coordinates in UTM44N.
    neigh_coords = read_CVFS_data(neighborhoods_coords_file, "NEIGHID") 

    neighborhoods = []
    for neigh_data in neigh_datas.itervalues():
        NEIGHID = int(neigh_data["NEIGHID"])
        neighborhood = model_world.new_neighborhood(NEIGHID, initial_agent=True)
        neighborhood._avg_years_nonfamily_services = float(neigh_data["AVG_YRS_SRVC"])
        neighborhood._elec_available =  bool(neigh_data['ELEC_AVAIL']) # is neighborhood electrified (in 1995/1996)
        # All land areas are given in square meters
        neighborhood._land_agveg = float(neigh_data['land.agveg'])
        neighborhood._land_nonagveg= float(neigh_data['land.nonagveg'])
        neighborhood._land_privbldg = float(neigh_data['land.privbldg'])
        neighborhood._land_pubbldg = float(neigh_data['land.pubbldg'])
        neighborhood._land_other = float(neigh_data['land.other'])
        neighborhood._land_total = neighborhood._land_agveg + \
                neighborhood._land_nonagveg + neighborhood._land_privbldg + \
                neighborhood._land_pubbldg + neighborhood._land_other
        neighborhood._x = float(neigh_coords[NEIGHID]['x'])
        neighborhood._y = float(neigh_coords[NEIGHID]['y'])
        neighborhoods.append(neighborhood)

    return neighborhoods

def assemble_households(householdsFile, model_world):
    """
    Reads in data from the CVFS (from dataset DS0002) on several statistics for 
    each household (BAA43, BAA44, BAA10A, BAA18A).
    """
    household_datas = read_CVFS_data(householdsFile, "HHID")
    
    households = []
    HHID_NEIGHID_map = {} # Links persons with their HHID
    for household_data in household_datas.itervalues():
        HHID = int(household_data['HHID'])
        NEIGHID = int(household_data['NEIGHID'])
        HHID_NEIGHID_map[HHID] = NEIGHID
        
        household = model_world.new_household(HHID, initial_agent=True)
        household._own_house_plot = bool(household_data['BAA43']) # does the household own the plot of land the house is on
        household._rented_out_land = int(household_data['BAA44']) # does the household rent out any land

        own_any_bari = bool(household_data['BAA10A']) # does the household own any bari land
        own_any_khet = bool(household_data['BAA18A']) # does the household own any khet land

        if own_any_bari or own_any_khet or household._own_household_plot:
            household._own_any_land = True
        else:
            household._own_any_land = False

        households.append(household)

    return households, HHID_NEIGHID_map

def assemble_persons(relationshipsFile, model_world):
    """
    Reads data in from the CVFS census (dataset DS0004 (restricted)) and from 
    the household relationship grid, CVFS DS0016 (restricted), which were 
    combined into one file, hhrel.csv, by the data_preprocess.R R script. This 
    function then assembles person agents from the data, including their 
    relationships (parent, child, etc.) with other agents.
    """
    relations = read_CVFS_data(relationshipsFile, "RESPID") 

    # For each household, create a SUBJECT -> RESPID mapping.  For example:
    # SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID
    SUBJECT_RESPID_map = {}
    for relation in relations.itervalues():
        RESPID = int(relation['RESPID'])
        SUBJECT = int(relation['SUBJECT'])
        HHID = int(relation['HHID'])
        if SUBJECT_RESPID_map.has_key(HHID):
            SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID
        else:
            SUBJECT_RESPID_map[HHID] = {}
            SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID

    # Loop over all agents in the relationship grid.
    personsDict = {}
    RESPID_HHID_map = {} # Links persons with their HHID
    # Get model starting time as this will be needed for setting last birth 
    # times
    model_start_time = rcParams['model.timebounds'][0]
    model_start_time = model_start_time[0] + model_start_time[1]/12.
    for relation in relations.itervalues():
        RESPID = int(relation['RESPID'])
        HHID = int(relation['HHID'])
        RESPID_HHID_map[RESPID] = HHID

        # Get the agent's sex and age
        try:
            AGEMNTHS = int(relation['AGEMNTHS']) # Age of agent in months
            CENGENDR = relation['CENGENDR']
        except KeyError:
            print "WARNING: no census data on person %s. This agent will be excluded from the model."%(RESPID)
            continue
        except ValueError:
            print "WARNING: no census data on person %s. This agent will be excluded from the model."%(RESPID)
            continue
        
        # Read in SUBJECT IDs of parents/spouse/children
        mother_SUBJECT = int(relation['PARENT1'])
        father_SUBJECT = int(relation['PARENT2'])
        spouse_SUBJECT = int(relation['SPOUSE1'])

        # Convert SUBJECT IDs into RESPIDs
        if father_SUBJECT != 0:
            try:
                father_RESPID = SUBJECT_RESPID_map[HHID][father_SUBJECT]
            except KeyError:
                print "WARNING: father of person %s was excluded from the model. Person %s will have their father field set to None."%(RESPID, RESPID)
        else:
            father_RESPID = None

        if mother_SUBJECT != 0:
            try:
                mother_RESPID = SUBJECT_RESPID_map[HHID][mother_SUBJECT]
            except KeyError:
                print "WARNING: mother of person %s was excluded from the model. Person %s will have their mother field set to None."%(RESPID, RESPID)
        else:
            mother_RESPID = None

        if spouse_SUBJECT != 0:
            try:
                spouse_RESPID = SUBJECT_RESPID_map[HHID][spouse_SUBJECT]
            except KeyError:
                print "WARNING: spouse of person %s was excluded from the model. Person %s will have their spouse field set to None."%(RESPID, RESPID)
                spouse_RESPID = None
        else:
            spouse_RESPID = None

        # Convert numerical genders to "male" or "female". 1 = male, 2 = female
        if CENGENDR == '1':
            CENGENDR = "male"
        elif CENGENDR == '2':
            CENGENDR = "female"

        # Finally, make the new person.
        person = model_world.new_person(None, RESPID, mother_RESPID, father_RESPID, AGEMNTHS, 
                CENGENDR, initial_agent=True)
        person._spouse = spouse_RESPID
        person._des_num_children = int(relation['numchild'])

        # If this person had a birth in the Nepali year 2053 in the LHC data, 
        # set the time of their last birth to 0 (equivalent to January 1996 in 
        # the model) so that they will not give birth again until after minimum 
        # birth interval has passed.
        recent_birth = int(relation['recentbirth'])
        if recent_birth == 1:
            person._last_birth_time = model_start_time
        else:
            # Otherwise, randomly set person._last_birth_time anywhere from 3 
            # years prior to the initial timestep of the model:
            person._last_birth_time = model_start_time + np.random.randint(-36, 0)/12.
        personsDict[RESPID] = person

    # Now, for each person in the personsDict, convert the RESPIDs for mother, 
    # father, and spouse to be references to the actual instances  of the 
    # mother, father and spouse agents.
    persons = []
    for person in personsDict.values():
        try:
            if person._mother != None:
                person._mother = personsDict[person._mother]
                if person._mother == person:
                    print "WARNING: agent %s skipped because it is it's own mother"%(person.get_ID())
                    continue
            if person._father != None:
                person._father = personsDict[person._father]
                if person._father == person:
                    print "WARNING: agent %s skipped because it is it's own father"%(person.get_ID())
                    continue
            if person._spouse != None:
                # First assign the person's spouse
                person._spouse = personsDict[person._spouse]
                # Set marriage time based on the yougest spouse's age, unless 
                # marriage time has already been set (if we have already looped 
                # over their spouse).
                if person._marriage_time == None:
                    if person._age < person._spouse._age:
                        youngests_age_mnths = person._age
                    else:
                        youngests_age_mnths = person._spouse._age
                    # Set marriage time based on the youngest spouse's age, as 
                    # a random number of years from 0-5 from the point at which 
                    # the woman was age 23. For women younger than 23, set 
                    # their marriage_time to the start time of the model.
                    if youngests_age_mnths/12 < 18:
                        marriage_time = model_start_time - (youngests_age_mnths / 
                                12) + 18 + np.random.randint(-24, 0) / 12.
                    elif youngests_age_mnths/12 < 23:
                        marriage_time = model_start_time - (youngests_age_mnths / 
                                12) + 23 + np.random.randint(-60, 0) / 12.
                    else:
                        marriage_time = model_start_time - (youngests_age_mnths / 
                                12) + 30 + np.random.randint(-144, 0) / 12.
                    person._marriage_time = marriage_time
                    person._spouse._marriage_time = marriage_time
                if person._spouse == person:
                    print "WARNING: agent %s skipped because it is married to itself"%(person.get_ID())
                    continue
            persons.append(person)
        except KeyError:
            print "WARNING: person %s skipped due to mother/father/spouse KeyError. This agent will be excluded from the model."%(person.get_ID())
    
    # Now run through all the person agents, and store each person agent in 
    # both of it's parent's child lists, so that the number of children each 
    # agent has can be accurately calculated.
    for person in persons:
        if person._father != None:
            person._father._children.append(person)
        if person._mother != None:
            person._mother._children.append(person)

    return persons, RESPID_HHID_map

def assemble_world():
    """
    Puts together a single world (with, currently, only a single region) from 
    the CVFS data using the above functions to input restricted CVFS data on 
    persons, households, and neighborhoods.
    """
    model_world = World()

    relationships_grid_file = rcParams['input.relationships_grid_file']
    households_file = rcParams['input.households_file']
    neighborhoods_file = rcParams['input.neighborhoods_file']
    neighborhoods_coords_file = rcParams['input.neighborhoods_coords_file']

    persons, RESPID_HHID_map = assemble_persons(relationships_grid_file,
            model_world)
    households, HHID_NEIGHID_map = assemble_households(households_file,
            model_world)
    neighborhoods = assemble_neighborhoods(neighborhoods_file,
            neighborhoods_coords_file, model_world)

    # Populate the Chitwan region (the code could handle multiple regions too, 
    # for instance, subdivide the population into different groups with 
    # different hazards of migration. Currently just one region is used.
    region = model_world.new_region()

    for neighborhood in neighborhoods:
        region.add_agent(neighborhood)

    # Now populate the neighborhoods with households. For this we need the HHID 
    # -> NID mapping:
    for household in households:
        HHID = household.get_ID()
        NEIGHID = HHID_NEIGHID_map[HHID]
        # Get a reference to this neighborhood, and add the household
        neighborhood = region.get_agent(NEIGHID)
        neighborhood.add_agent(household, initializing=True)

    # Now populate the households with people. For this we need the RESPID -> 
    # HHID mapping and the HHID -> NEIGHID map.
    for person in persons:
        RESPID = person.get_ID()
        HHID = RESPID_HHID_map[RESPID]
        try:
            NEIGHID = HHID_NEIGHID_map[HHID]
        except KeyError:
            print "WARNING: household %s is not in DS0002. This agent will be excluded from the model."%(HHID)
            continue
        # Get a reference to this neighborhood
        neighborhood = region.get_agent(NEIGHID)
        # Then get a reference to the proper household, and add the person
        household = neighborhood.get_agent(HHID)
        household.add_agent(person)

    print "\nPersons: %s, Households: %s, Neighborhoods: %s"%(region.num_persons(), region.num_households(), region.num_neighborhoods())
    return model_world

def save_world(world, filename):
    "Pickles a world for later reloading."
    file = open(filename, "w")
    pickle.dump(world, file)

def generate_world():
    """
    Performs the complete process necessary for initializing the model from    
    CVFS restricted data.
        1) Calls the necessary R script for preparing the necessary CSV 
        initialization files from the CVFS data. 

        2) Calls the assemble_world function to prepare an instance of the 
        World class to be used in the model.

        3) Saves this world instange in the standard location. NOTE: This must 
        be an encrypted directory that is not publically accessible to conform 
        to ICPSR and IRB requirements.
    """
    input_init_data_file = rcParams['input.init_data_file']
    try:
        print "Calling R to preprocess CVFS data..."
        check_call(["/usr/bin/Rscript", "data_preprocess.R"])
    except CalledProcessError:
        print "error running data_preprocess.R R script"
    print "Generating world from preprocessed CVFS data..."
    model_world = assemble_world()
    try:
        save_world(model_world, input_init_data_file)
    except:
        print "error saving world file to %s"%(input_init_data_file)

if __name__ == "__main__":
    sys.exit(main())
