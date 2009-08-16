"""
Part of Chitwan Valley agent-based model.

Contains main model loop: Contains the main loop for the model. Takes input 
parameters read from runModel.py, and passes results of model run back.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import time
import copy

import numpy as np

from ChitwanABM import rcParams
from ChitwanABM.eventtracking import Results

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

    def increment(self):
        assert self._month != 0, "Month cannot be 0"
        self._month += self._timestep
        dyear = int((self._month - 1) / 12)
        self._year += dyear
        self._month = self._month - dyear*12

    def in_bounds(self):
        if self._year == self._endtime[0] and self._month >= self._endtime[1] \
                or self._year > self._endtime[0]:
            return False
        else:
            return True
    
    def get_cur_month(self):
        return self._month

    def get_cur_date(self):
        return [self._year, self._month]

    def get_cur_date_float(self):
        return self._year + (self._month-1)/12.

    def __str__(self):
        return "%s-%s"%(self._year, self._month)


timebounds = rcParams['model.timebounds']
timestep = rcParams['model.timestep']

model_time = TimeSteps(timebounds, timestep)

def main_loop(world):
    """This function contains the main model loop. Passed to it is a list of 
    regions, which contains the person, household, and neighborhood agents to 
    be used in the model, and the land-use parameters."""

    # saved_data will store the results of each timestep.
    saved_data = Results()
    
    # Save the starting time of the model to use in printing elapsed time while 
    # it runs.
    modelrun_starttime = time.time()

    while model_time.in_bounds():
        saved_data.add_timestep(model_time.get_cur_date_float())
        
        if model_time.get_cur_month() == 1 or \
                model_time.get_cur_date() == model_time._starttime:
            print "  TOTAL | New Ma: %3s | B: %3s | D: %3s | Mi: %3s"%(
                    sum(saved_data._num_marriages[-13:-1]),
                    sum(saved_data._num_births[-13:-1]),
                    sum(saved_data._num_deaths[-13:-1]),
                    sum(saved_data._num_migrations[-13:-1]))
            msg = "Elapsed time: %11s"%elapsed_time(modelrun_starttime)
            msg = msg.rjust(80)
            print msg

        for region in world.iter_regions():
            # This could easily handle multiple regions, although currently 
            # there is only one, for all of Chitwan.
            #print "Num marriages:", 
            num_new_births = region.births(model_time.get_cur_date_float())
            num_new_deaths = region.deaths(model_time.get_cur_date_float())
            num_new_marriages = region.marriages(model_time.get_cur_date_float())
            num_new_migrations = region.migrations(model_time.get_cur_date_float())
            landuse = region.update_landuse(model_time.get_cur_date_float())

            num_persons = region.num_persons()
            num_households = region.num_households()
            num_neighborhoods = region.num_neighborhoods()

            # store results:
            saved_data.add_num_births(num_new_births)
            saved_data.add_num_deaths(num_new_deaths)
            saved_data.add_num_marriages(num_new_marriages)
            saved_data.add_num_migrations(num_new_migrations)
            saved_data.add_num_persons(num_persons)
            saved_data.add_num_households(num_households)
            saved_data.add_num_neighborhoods(num_neighborhoods)

            region.increment_age()
                
        print "%s | P: %5s | TMa: %5s | HH: %5s | Ma: %3s | B: %3s | D: %3s | Mi: %3s"%(
                str(model_time).ljust(7), num_persons, region.get_num_marriages(), num_households,
                num_new_marriages, num_new_births, num_new_deaths, num_new_migrations)

        if num_persons == 0:
            print "End of model run: population is zero."
            break

        model_time.increment()

    return saved_data

def elapsed_time(start_time):
    elapsed = int(time.time() - start_time)
    hours = elapsed / 3600
    minutes = (elapsed - hours * 3600) / 60
    seconds = elapsed - hours * 3600 - minutes * 60
    return "%ih %im %is" %(hours, minutes, seconds)
