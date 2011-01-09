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
Contains main model loop: Contains the main loop for the model. Takes input 
parameters read from runModel.py, and passes results of model run back.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import os
import time
import copy

import numpy as np

from ChitwanABM import file_io
from ChitwanABM import rcParams

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

class TimeSteps():
    def __init__(self, bounds, timestep):
        self._starttime = bounds[0]
        self._endtime = bounds[1]
        self._timestep = timestep

        # Initialize the current month and year
        self._year = self._starttime[0]
        self._month = self._starttime[1]
        self._int_timestep = 1

    def increment(self):
        self._month += self._timestep
        dyear = int((self._month - 1) / 12)
        self._year += dyear
        self._month = self._month - dyear*12
        self._int_timestep += 1
        assert self._month != 0, "Month cannot be 0"

    def in_bounds(self):
        if self._year == self._endtime[0] and self._month >= self._endtime[1] \
                or self._year > self._endtime[0]:
            return False
        else:
            return True

    def is_last_iteration(self):
        next_month = self._month + self._timestep
        dyear = int((next_month - 1) / 12)
        next_year = self._year + dyear
        next_month = next_month - dyear*12
        if next_year >= self._endtime[0] and next_month >= self._endtime[1]:
            return True
        else:
            return False
    
    def get_cur_month(self):
        return self._month

    def get_cur_year(self):
        return self._year

    def get_cur_date(self):
        return [self._year, self._month]

    def get_cur_date_string(self):
        return "%.2d/%s"%(self._month, self._year)

    def get_cur_date_float(self):
        return self._year + (self._month-1)/12.

    def get_cur_int_timestep(self):
        return self._int_timestep

    def __str__(self):
        return "%s-%s"%(self._year, self._month)


timebounds = rcParams['model.timebounds']
timestep = rcParams['model.timestep']

model_time = TimeSteps(timebounds, timestep)

def main_loop(world, results_path):
    """This function contains the main model loop. Passed to it is a list of 
    regions, which contains the person, household, and neighborhood agents to 
    be used in the model, and the land-use parameters."""

    time_strings = {}
    time_strings['timestep'] = []
    time_strings['time_float'] = []
    time_strings['time_date'] = []

    saved_LULC_results = {}

    # Keep annual totals to print while the model is running
    annual_num_marr = 0
    annual_num_births = 0
    annual_num_deaths = 0
    annual_num_in_migr = 0
    annual_num_out_migr = 0

    # saved_data will store the results of each timestep to be saved later as a 
    # CSV.
    saved_data = {}

    # Save the starting time of the model to use in printing elapsed time while 
    # it runs.
    modelrun_starttime = time.time()
    while model_time.in_bounds():
        
        if model_time.get_cur_month() == 1 or model_time.is_last_iteration():
            annual_num_births = 0
            annual_num_deaths = 0
            annual_num_marr = 0
            annual_num_in_migr = 0
            annual_num_out_migr = 0
            if rcParams['save_psn_data']:
                world.write_persons_to_csv(model_time.get_cur_int_timestep(), results_path)
            if rcParams['save_NBH_data']:
                world.write_NBHs_to_csv(model_time.get_cur_int_timestep(), results_path)
            if rcParams['save_LULC_shapefiles']:
                NBH_shapefile = os.path.join(results_path, "NBHs_time_%s.shp"%model_time.get_cur_int_timestep())
                neighborhoods = []
                regions = world.get_regions()
                for region in regions:
                    neighborhoods.extend(region.get_agents())
                file_io.write_NBH_shapefile(neighborhoods, NBH_shapefile)

        for region in world.iter_regions():
            # This could easily handle multiple regions, although currently 
            # there is only one, for all of Chitwan.
            new_births = region.births(model_time.get_cur_date_float())
            new_deaths = region.deaths(model_time.get_cur_date_float())
            new_marr = region.marriages(model_time.get_cur_date_float())
            new_out_migr, new_in_migr = region.migrations(model_time.get_cur_date_float())

            num_persons = region.num_persons()
            num_households = region.num_households()
            num_neighborhoods = region.num_neighborhoods()

            # Store results:
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

            # Save LULC data in a dictionary keyed by timestep:nbh:variable
            saved_LULC_results[model_time.get_cur_int_timestep()] = region.get_neighborhood_landuse()

            # Save event and population data for later output to CSV.
            saved_data[model_time.get_cur_int_timestep()] = {}
            saved_data[model_time.get_cur_int_timestep()]['births'] = new_births
            saved_data[model_time.get_cur_int_timestep()]['deaths'] = new_deaths
            saved_data[model_time.get_cur_int_timestep()]['marr'] = new_marr
            saved_data[model_time.get_cur_int_timestep()]['in_migr'] = new_in_migr
            saved_data[model_time.get_cur_int_timestep()]['out_migr'] = new_out_migr
            saved_data[model_time.get_cur_int_timestep()].update(region.get_neighborhood_pop_stats())
            saved_data[model_time.get_cur_int_timestep()].update(region.get_neighborhood_fw_usage())

            region.increment_age()
                
        # Print an information line to allow keeping tabs on the model while it 
        # is running.
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
            total_string = "TOTAL | New Ma: %3s | B: %3s | D: %3s | InMi: %3s | OutMi: %3s"%(
                    annual_num_marr, annual_num_births,
                    annual_num_deaths, annual_num_in_migr, annual_num_out_migr)
            total_string = total_string.center(len(stats_string))
            print total_string
            msg = "Elapsed time: %11s"%elapsed_time(modelrun_starttime)
            msg = msg.rjust(len(stats_string))
            print msg

        if num_persons == 0:
            print "End of model run: population is zero."
            break

        model_time.increment()

    return saved_data, saved_LULC_results, time_strings

def elapsed_time(start_time):
    elapsed = int(time.time() - start_time)
    hours = elapsed / 3600
    minutes = (elapsed - hours * 3600) / 60
    seconds = elapsed - hours * 3600 - minutes * 60
    return "%ih %im %is" %(hours, minutes, seconds)
