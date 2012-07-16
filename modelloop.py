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
Contains main model loop: Contains the main loop for the model. Takes input 
parameters read from runModel.py, and passes results of model run back.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import os
import time
import copy

import numpy as np

from PyABM import file_io
from PyABM.utility import TimeSteps
from ChitwanABM import rcParams

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

timebounds = rcParams['model.timebounds']
timestep = rcParams['model.timestep']

model_time = TimeSteps(timebounds, timestep)

def main_loop(world, results_path):
    """This function contains the main model loop. Passed to it is a list of 
    regions, which contains the person, household, and neighborhood agents to 
    be used in the model, and the land-use parameters."""

    time_strings = {}
    # Store the date values (as timestep number (0),  float and date string) 
    # for time zero (T0) so that the initial values of the model (which are for 
    # time zero, the zeroth timestep) can be used in plotting model results.
    time_strings['timestep'] = [0]
    time_strings['time_float'] = [model_time.get_T0_date_float()]
    time_strings['time_date'] = [model_time.get_T0_date_string()]

    # Keep annual totals to print while the model is running
    annual_num_marr = 0
    annual_num_births = 0
    annual_num_deaths = 0
    annual_num_in_migr = 0
    annual_num_out_migr = 0

    # Save the starting time of the model to use in printing elapsed time while 
    # it runs.
    modelrun_starttime = time.time()

    def write_results_CSV(world, results_path, timestep):
        """
        Function to periodically save model results to CSV (if this option is 
        selected in the rc file).
        """
        if rcParams['save_psn_data']:
            world.write_persons_to_csv(timestep, results_path)
        if rcParams['save_NBH_data']:
            world.write_NBHs_to_csv(timestep, results_path)
        if rcParams['save_LULC_shapefiles']:
            NBH_shapefile = os.path.join(results_path, "NBHs_time_%s.shp"%timestep)
            neighborhoods = []
            regions = world.get_regions()
            for region in regions:
                neighborhoods.extend(region.get_agents())
            file_io.write_NBH_shapefile(neighborhoods, NBH_shapefile)

    # Write the results for timestep 0
    write_results_CSV(world, results_path, 0)

    def save_data_dict(saved_data, timestep, date_float, region, new_births, 
            new_deaths, new_marr, new_out_migr, new_in_migr):
        """
        Store model results for later plotting. Store each variable in a 
        dictionary data while the model is runningthe data keyed by: 
        timestep:variable:nbh.
        """
        saved_data[timestep] = {}
        saved_data[timestep]['births'] = new_births
        saved_data[timestep]['deaths'] = new_deaths
        saved_data[timestep]['marr'] = new_marr
        saved_data[timestep]['in_migr'] = new_in_migr
        saved_data[timestep]['out_migr'] = new_out_migr
        saved_data[timestep].update(region.get_neighborhood_pop_stats())
        saved_data[timestep].update(region.get_neighborhood_fw_usage(date_float))
        saved_data[timestep].update(region.get_neighborhood_landuse())

    # saved_data will store event, population, and fuelwood usage data keyed by 
    # timestep:variable:nbh.
    saved_data = {}
    # Save the initialization data for timestep 0 (note that all the event 
    # variables, like new_births, new_deaths, etc., need to be set to None
    # in each neighborhood, for each variable, as they are unknown for timestep 
    # 0 (since the model has not yet begun). Need to construct an empty_events 
    # dictionary to initialize these events for timestep 0.
    # TODO: Fix this to work for multiple regions.
    region = world.get_regions()[0]
    empty_events = {}
    for neighborhood in region.iter_agents():
        empty_events[neighborhood.get_ID()] = np.NaN
    save_data_dict(saved_data, 0, 0, region, empty_events, empty_events,
            empty_events, empty_events, empty_events)

    while model_time.in_bounds():
        if model_time.get_cur_month() == 1:
            annual_num_births = 0
            annual_num_deaths = 0
            annual_num_marr = 0
            annual_num_in_migr = 0
            annual_num_out_migr = 0

        for region in world.iter_regions():
            # This could easily handle multiple regions, although currently 
            # there is only one, for all of Chitwan.
            new_births = region.births(model_time.get_cur_date_float())
            new_deaths = region.deaths(model_time.get_cur_date_float())
            new_marr = region.marriages(model_time.get_cur_date_float())
            new_out_migr, return_migr, new_in_migr = region.migrations(model_time.get_cur_date_float())
            schooling = region.education(model_time.get_cur_date_float())

            # Save event, LULC, and population data for later output to CSV.
            save_data_dict(saved_data, model_time.get_cur_int_timestep(), 
                    model_time.get_cur_date_float(), region, new_births, 
                    new_deaths, new_marr, new_out_migr,
                    new_in_migr)

            # Keep running total for printing results:
            num_new_births = sum(new_births.values())
            num_new_deaths = sum(new_deaths.values())
            num_new_marr = sum(new_marr.values())
            num_new_out_migr = sum(new_out_migr.values())
            num_new_in_migr = sum(new_in_migr.values())

            annual_num_births += num_new_births
            annual_num_deaths += num_new_deaths
            annual_num_marr += num_new_marr
            annual_num_in_migr += num_new_in_migr
            annual_num_out_migr += num_new_out_migr

            region.increment_age()
                
        # Print an information line to allow keeping tabs on the model while it 
        # is running.
        num_persons = region.num_persons()
        num_households = region.num_households()
        stats_string = "%s | P: %5s | TMa: %5s | HH: %5s | Ma: %3s | B: %3s | D: %3s | InMi: %3s | OutMi: %3s"%(
                model_time.get_cur_date_string().ljust(7), num_persons, region.get_num_marriages(), num_households,
                num_new_marr, num_new_births, num_new_deaths, num_new_in_migr, num_new_out_migr)
        print stats_string

        # Save timestep, year and month, and time_float values for use in 
        # storing results (to CSV) keyed to a particular timestep.
        time_strings['timestep'].append(model_time.get_cur_int_timestep())
        time_strings['time_float'].append(model_time.get_cur_date_float())
        time_strings['time_date'].append(model_time.get_cur_date_string())

        if model_time.get_cur_month() == 12 or model_time.is_last_iteration() \
                and model_time.get_cur_date() != model_time._starttime:
            # The last condition in the above if statement is necessary as 
            # there is no total to print on the first timestep, so it wouldn't 
            # make sense to print it.
            total_string = "%s TOTAL | New Ma: %3s | B: %3s | D: %3s | InMi: %3s | OutMi: %3s"%(
                    model_time.get_cur_year(), annual_num_marr, annual_num_births,
                    annual_num_deaths, annual_num_in_migr, annual_num_out_migr)
            total_string = total_string.center(len(stats_string))
            print total_string
            msg = "Elapsed time: %11s"%elapsed_time(modelrun_starttime)
            msg = msg.rjust(len(stats_string))
            print msg

        if num_persons == 0:
            print "End of model run: population is zero."
            break

        if model_time.get_cur_month() == 12 or model_time.is_last_iteration():
            write_results_CSV(world, results_path, model_time.get_cur_int_timestep())

        model_time.increment()

    return saved_data, time_strings

def elapsed_time(start_time):
    elapsed = int(time.time() - start_time)
    hours = elapsed / 3600
    minutes = (elapsed - hours * 3600) / 60
    seconds = elapsed - hours * 3600 - minutes * 60
    return "%ih %im %is" %(hours, minutes, seconds)
