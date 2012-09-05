#!/usr/bin/env python
# Copyright 2008-2012 Alex Zvoleff
# 
# This file is part of the chitwanabm agent-based model.
# 
# chitwanabm is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# chitwanabm is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# chitwanabm.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff (azvoleff@mail.sdsu.edu) in the Department of Geography 
# at San Diego State University with any comments or questions. See the 
# README.txt file for contact information.
"""
Sets up a chitwanabm model run: Initializes neighborhood/household/person agents 
and land use using the original CVFS data.
"""

from __future__ import division

import os
import sys
import logging
import pickle
from pkg_resources import resource_filename
from subprocess import check_call, CalledProcessError

import numpy as np

from pyabm.file_io import read_single_band_raster

from chitwanabm import rc_params
from chitwanabm.agents import World

logger = logging.getLogger(__name__)

rcParams = rc_params.get_params()

def main():
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    log_console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
            datefmt='%I:%M:%S%p')
    ch.setFormatter(log_console_formatter)
    logger.addHandler(ch)

    world = generate_world()
    if world == 1:
        logger.critical("Problem generating world")
        return 1

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
        logger.exception("Error reading %s"%textfile)
        return 1
    
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
        if data_key in new_data:
            logger.critical("Error reading %s: key %s is already in use"%(textfile, data_key))
            return 1
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
        neighborhood._avg_yrs_services_lt15 = float(neigh_data["avg_yrs_services_lt15"])
        neighborhood._avg_yrs_services_lt30 = float(neigh_data["avg_yrs_services_lt30"])
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

        neighborhood._forest_dist_BZ_km = float(neigh_data['BZ_meters']) / 1000.
        neighborhood._forest_dist_CNP_km = float(neigh_data['CNP_meters']) / 1000.
        neighborhood._forest_closest_km = float(neigh_data['closest_meters']) / 1000.
        neighborhood._forest_closest_type = neigh_data['closest_type']

        neighborhood._school_min_ft = float(neigh_data['SCHLFT52'])
        neighborhood._health_min_ft = float(neigh_data['HLTHFT52'])
        neighborhood._bus_min_ft = float(neigh_data['BUSFT52'])
        neighborhood._market_min_ft = float(neigh_data['MARFT52'])
        neighborhood._employer_min_ft = float(neigh_data['EMPFT52'])

        neighborhood._x = float(neigh_coords[NEIGHID]['x'])
        neighborhood._y = float(neigh_coords[NEIGHID]['y'])
        neighborhood._distnara =  float(neigh_data['dist_nara']) # distance from Narayanghat
        neighborhoods.append(neighborhood)

    return neighborhoods

def assemble_households(householdsFile, model_world):
    """
    Reads in data from the CVFS (from dataset DS0002) on several statistics for 
    each household (BAA43, BAA44, BAA10A, BAA18A).
    """
    household_datas = read_CVFS_data(householdsFile, "HHID")
    
    model_start_time = rcParams['model.timebounds'][0]
    model_start_time = model_start_time[0] + model_start_time[1]/12.

    households = []
    HHID_NEIGHID_map = {} # Links persons with their HHID
    for household_data in household_datas.itervalues():
        HHID = int(household_data['HHID'])
        NEIGHID = int(household_data['NEIGHID'])
        HHID_NEIGHID_map[HHID] = NEIGHID
        
        household = model_world.new_household(HID=HHID, initial_agent=True)
        household._own_house_plot = bool(household_data['BAA43']) # does the household own the plot of land the house is on
        household._rented_out_land = int(household_data['BAA44']) # does the household rent out any land


        # Roughly a third of households will have had a person make an LD 
        # migration within the last year:
        if np.random.rand() < .4:
            household._lastmigrant_time = model_start_time + np.random.randint(-12, 0)/12.
        else:
            household._lastmigrant_time = -9999

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
        if HHID in SUBJECT_RESPID_map:
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
    # The extra spouses list will contain a list of second and third spouses - 
    # these spouses will have their status set to unmarried as the model does 
    # not allow having more than one spouse.
    extra_spouses = []
    for relation in relations.itervalues():
        RESPID = int(relation['RESPID'])
        HHID = int(relation['HHID'])
        RESPID_HHID_map[RESPID] = HHID

        # Get the agent's sex and age
        try:
            AGEMNTHS = int(relation['AGEMNTHS']) # Age of agent in months
            CENGENDR = relation['CENGENDR']
            ETHNICITY = int(relation['ETHNIC'])
        except KeyError, ValueError:
            logger.warning("Person %s skipped because they are not in the census"%RESPID)
            continue
        
        # Read in SUBJECT IDs of parents/spouse/children
        mother_SUBJECT = int(relation['PARENT1'])
        father_SUBJECT = int(relation['PARENT2'])
        spouse_1_SUBJECT = int(relation['SPOUSE1'])
        # Also read in spouse 2 and spouse 3 ID so that these spouses can be 
        # excluded from the model.
        spouse_2_SUBJECT = int(relation['SPOUSE2'])
        spouse_3_SUBJECT = int(relation['SPOUSE3'])

        # Convert SUBJECT IDs into RESPIDs
        if father_SUBJECT != 0:
            try:
                father_RESPID = SUBJECT_RESPID_map[HHID][father_SUBJECT]
            except KeyError:
                father_RESPID = None
                logger.warning("Father of person %s was excluded from the model - father field set to None"%RESPID)
        else:
            father_RESPID = None

        if mother_SUBJECT != 0:
            try:
                mother_RESPID = SUBJECT_RESPID_map[HHID][mother_SUBJECT]
            except KeyError:
                mother_RESPID = None
                logger.warning("Mother of person %s was excluded from the model - mother field set to None"%RESPID)
        else:
            mother_RESPID = None

        if spouse_1_SUBJECT != 0:
            try:
                spouse_RESPID = SUBJECT_RESPID_map[HHID][spouse_1_SUBJECT]
            except KeyError:
                spouse_RESPID = None
                logger.warning("Spouse of person %s was excluded from the model - spouse field set to None"%RESPID)
        else:
            spouse_RESPID = None

        if spouse_2_SUBJECT != 0:
            try:
                spouse_2_RESPID = SUBJECT_RESPID_map[HHID][spouse_2_SUBJECT]
                extra_spouses.append(spouse_2_RESPID)
            except KeyError:
                logger.warning("Spouse two of person %s was excluded from the model"%RESPID)

        if spouse_3_SUBJECT != 0:
            try:
                spouse_3_RESPID = SUBJECT_RESPID_map[HHID][spouse_3_SUBJECT]
                extra_spouses.append(spouse_3_RESPID)
            except KeyError:
                logger.warning("Spouse three of person %s was excluded from the model"%RESPID)

        # Convert numerical genders to "male" or "female". 1 = male, 2 = female
        if CENGENDR == '1':
            CENGENDR = "male"
        elif CENGENDR == '2':
            CENGENDR = "female"

        if ETHNICITY == 1:
            ETHNICITY = "HighHindu"
        elif ETHNICITY == 2:
            ETHNICITY = "HillTibeto"
        elif ETHNICITY == 3:
            ETHNICITY = "LowHindu"
        elif ETHNICITY == 4:
            ETHNICITY = "Newar"
        elif ETHNICITY == 5:
            ETHNICITY = "TeraiTibeto"
        assert ETHNICITY!=6, "'Other' ethnicity should be dropped from the model"

        # Finally, make the new person.
        person = model_world.new_person(None, PID=RESPID, mother=mother_RESPID, 
                father=father_RESPID, age=AGEMNTHS, sex=CENGENDR, 
                initial_agent=True, ethnicity=ETHNICITY)
        person._spouse = spouse_RESPID
        person._des_num_children = int(relation['desnumchild'])
        person._schooling = int(relation['schooling'])

        person._child_school_lt_1hr_ft = int(relation['child_school_1hr'])
        person._child_health_lt_1hr_ft = int(relation['child_health_1hr'])
        person._child_bus_lt_1hr_ft = int(relation['child_bus_1hr'])
        person._child_employer_lt_1hr_ft = int(relation['child_emp_1hr'])
        person._child_market_lt_1hr_ft = int(relation['child_market_1hr'])

        person._parents_contracep_ever = int(relation['parents_contracep_ever'])

        person._father_work = int(relation['father_work'])
        person._father_years_schooling = int(relation['father_school'])
        person._mother_work = int(relation['mother_work'])
        person._mother_years_schooling = int(relation['mother_school'])
        person._mother_num_children = int(relation['mother_num_children'])

        marr_time = relation['marr_date']
        if marr_time == 'NA':
            person._marriage_time = None
        else:
            person._marriage_time = float(marr_time)

        # If this person had a birth in the Nepali year 2053 in the LHC data, 
        # set the time of their last birth to 0 (equivalent to January 1996 in 
        # the model) so that they will not give birth again until after minimum 
        # birth interval has passed.
        recent_birth = int(relation['recent_birth'])
        if recent_birth == 1:
            person._last_birth_time = model_start_time
        else:
            # Otherwise, randomly set person._last_birth_time anywhere from 18
            # months prior to the initial timestep of the model:
            person._last_birth_time = model_start_time + np.random.randint(-24, 0)/12.
        personsDict[RESPID] = person

        n_children = int(relation['n_children'])
        person._number_of_children = n_children

    # Ignore second and third spouses, as the model does not allow them.
    for extra_spouse in extra_spouses:
        personsDict[extra_spouse]._spouse = None

    # Now, for each person in the personsDict, convert the RESPIDs for mother, 
    # father, and spouse to be references to the actual instances  of the 
    # mother, father and spouse agents.
    persons = []
    for person in personsDict.values():
        try:
            if person._mother != None:
                person._mother = personsDict[person._mother]
                if person._mother == person:
                    logger.warning("Person %s skipped because it is it's own mother"%(person.get_ID()))
                    continue
            if person._father != None:
                person._father = personsDict[person._father]
                if person._father == person:
                    logger.warning("Person %s skipped because it is it's own father"%(person.get_ID()))
                    continue
            if person._spouse != None:
                # First assign the person's spouse
                person._spouse = personsDict[person._spouse]
                # If marriage time is unknown, set marriage time based on the 
                # youngest spouse's age, unless marriage time has already been 
                # set (if we have already looped over their spouse).
                if person._marriage_time == None:
                    if person._agemonths < person._spouse._agemonths:
                        youngests_age_mnths = person._agemonths
                    else:
                        youngests_age_mnths = person._spouse._agemonths
                    # Set marriage time based on the youngest spouse's age, as 
                    # a random age (for the youngest spouse) between 15 - and 
                    # the youngest spouse age or 27 (whichever is smaller).
                    if youngests_age_mnths/12. < 15:
                        marriage_time = model_start_time
                    else:
                        if youngests_age_mnths/12. < 27:
                            max_marr_age = youngests_age_mnths/12.
                        else:
                            max_marr_age = 27.
                        marriage_age_mnths = np.random.randint(15, max_marr_age)*12.
                        marriage_time = model_start_time - (youngests_age_mnths -
                                marriage_age_mnths) / 12.
                    person._marriage_time = marriage_time
                    person._spouse._marriage_time = marriage_time
                if person._spouse == person:
                    logger.warning("Person %s skipped because it is married to itself"%(person.get_ID()))
                    continue
            persons.append(person)
        except KeyError:
            logger.warning("Person %s skipped due to mother/father/spouse KeyError"%(person.get_ID()))
    
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

    raw_data_path = rcParams['path.raw_input_data']
    relationships_grid_file = os.path.join(raw_data_path, 'hhrel.csv')
    households_file = os.path.join(raw_data_path, 'hhag.csv')
    neighborhoods_file = os.path.join(raw_data_path,  'neigh.csv')
    neighborhoods_coords_file = os.path.join(raw_data_path, 'neigh_coords.csv')

    persons, RESPID_HHID_map = assemble_persons(relationships_grid_file,
            model_world)
    households, HHID_NEIGHID_map = assemble_households(households_file,
            model_world)
    neighborhoods = assemble_neighborhoods(neighborhoods_file,
            neighborhoods_coords_file, model_world)

    for neighborhood in neighborhoods:
        # To each neighborhood, add a list of IDs of the other neighborhoods, 
        # sorted by their distance to this neighborhood:
        this_x = neighborhood._x
        this_y = neighborhood._y
        neighborhood._neighborhoods_by_distance = sorted(neighborhoods, key=lambda neighborhood: \
                np.sqrt((neighborhood._x - this_x)**2 + (neighborhood._y - this_y)**2))
        # Now remove this neighborhood (in the first position) from the list.  
        # We already know that the closest neighborhood is itself.
        neighborhood._neighborhoods_by_distance.pop(0)

    # Add the DEM and CVFS Study Area mask to the model_world instance.
    DEM_file = os.path.join(raw_data_path, rcParams['path.DEM_file'])
    DEM, gt, prj = read_single_band_raster(DEM_file)
    model_world.set_DEM_data(DEM, gt, prj)

    world_mask_file = os.path.join(raw_data_path, rcParams['path.world_mask'])
    world_mask, gt, prj = read_single_band_raster(world_mask_file)
    model_world.set_world_mask_data(world_mask, gt, prj)

    # Populate the Chitwan region (the code could handle multiple regions too, 
    # for instance, subdivide the population into different groups with 
    # different probabilites of migration, death, mortality, etc. Currently 
    # just one region is used.
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
            logger.warning("Household %s skipped because it is not in DS0002"%(HHID))
            continue
        # Get a reference to this neighborhood
        neighborhood = region.get_agent(NEIGHID)
        # Then get a reference to the proper household, and add the person
        household = neighborhood.get_agent(HHID)
        household.add_agent(person)

    # Now check that there are no empty households and no empty neighborhoods.  
    # Empty households or neighborhoods could occur due to people excluded due 
    # to missing data, or due to people excluded because of their ethnicity.
    for region in model_world.iter_regions():
        for neighborhood in region.iter_agents():
            for household in neighborhood.iter_agents():
                if household.num_members() == 0:
                    logger.warning("Household %s skipped because it has no members"%(household.get_ID()))
                    neighborhood.remove_agent(household)
    for region in model_world.iter_regions():
        for neighborhood in region.iter_agents():
            if neighborhood.num_members() == 0:
                logger.warning("Neighborhood %s skipped because it has no members"%(neighborhood.get_ID()))
                continue

    logger.info("World generated with %s persons, %s households, and %s neighborhoods"%(region.num_persons(), region.num_households(), region.num_neighborhoods()))
    return model_world

def save_world(world, filename):
    "Pickles a world for later reloading."
    file = open(filename, "w")
    pickle.dump(world, file)

def generate_world():
    """
    Performs the complete process necessary for initializing the model from    
    CVFS restricted data.

        1) Calls the necessary R script  (data_preprocess.R) for preparing the 
        necessary CSV initialization files from the CVFS data. 

        2) Calls the assemble_world function to prepare an instance of the 
        World class to be used in the model.

        3) Saves this World instance in the specified location. NOTE: This must 
        be an encrypted directory that is not publically accessible to conform 
        to ICPSR and IRB requirements.
    """
    try:
        logger.info("Calling R to preprocess CVFS data")
        raw_data_path = rcParams['path.raw_input_data']
        Rscript_binary = rcParams['path.Rscript_binary']
        preprocess_script = resource_filename(__name__, 'R/data_preprocess.R')
        check_call([Rscript_binary, preprocess_script, raw_data_path, 
            str(rcParams['random_seed'])])
    except CalledProcessError:
        logger.exception("Problem while running data_preprocess.R R script")
        return 1
    logger.info("Generating world from preprocessed CVFS data")
    model_world = assemble_world()

    try:
        processed_data_file = rcParams['path.input_data_file']
        save_world(model_world, processed_data_file)
        logger.info("World file saved to %s"%processed_data_file)
    except:
        logger.error("Problem saving world file to %s"%processed_data_file)

    return model_world

if __name__ == "__main__":
    sys.exit(main())
