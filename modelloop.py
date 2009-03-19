"""
Part of Chitwan Valley agent-based model.

Contains main model loop: Contains the main loop for the model. Takes input 
parameters read from runModel.py, and passes results of model run back.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import time
import copy

import numpy as np

from chitwanABM import rcParams
from chitwanABM.eventtracking import Results

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

timezero = rcParams['model.timezero']
endtime = rcParams['model.endtime']
timestep = rcParams['model.timestep']
timesteps = np.arange(timezero, endtime, timestep)

def main_loop(region):
    """This function contains the main model loop. Passed to it is a list of 
    regions, which contains the person, household, and neighborhood agents to 
    be used in the model, and the land-use parameters."""

    # saved_data will store the results of each timestep.
    saved_data = Results()
    
    # Save the starting time of the model to use in printing elapsed time while 
    # it runs.
    modelrun_starttime = time.time()

    for t in timesteps:
        saved_data.add_timestep(t)

        # The weird expression below is needed to handle the imprecision of 
        # machine representation of floating point numbers.
        if (np.ceil(t) - t) <= .001:
            print "Elapsed time: ", elapsed_time(modelrun_starttime) + "\n"
            print "Model  time:", str(t)
        # This could easily be written to handle multiple regions, although 
        # currently there is only one, for all of Chitwan.
        num_births = region.births(t)
        num_deaths = region.deaths(t)
        num_marriages = region.marriages(t)
        num_migrations = region.migrations(t)
        region.update_landuse(t)

        num_persons = region.num_persons()
        num_households = region.num_households()
        num_neighborhoods = region.num_neighborhoods()

        # store results:
        saved_data.add_num_births(num_births)
        saved_data.add_num_deaths(num_deaths)
        saved_data.add_num_marriages(num_marriages)
        saved_data.add_num_migrations(num_migrations)
        saved_data.add_num_persons(num_persons)
        saved_data.add_num_households(num_households)
        saved_data.add_num_neighborhoods(num_neighborhoods)

        region.increment_age()
            
        num_persons = region.num_persons()

        if num_persons == 0:
            print "End of model run: population is zero."

        print "    Pop: %s\tBirths: %s\tDeaths: %s\tMarr: %s\tMigr: %s"%(
                num_persons, num_births, num_deaths, num_marriages, num_migrations)

    return saved_data

def elapsed_time(start_time):
    elapsed = int(time.time() - start_time)
    hours = elapsed / 3600
    minutes = (elapsed - hours * 3600) / 60
    seconds = elapsed - hours * 3600 - minutes * 60
    return "%ih %im %is" %(hours, minutes, seconds)
