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
    saved_data = []
    
    # Save the starting time of the model to use in printing elapsed time while 
    # it runs.
    modelrun_starttime = time.time()
    # The run_ID_number provides an ID number (built from the start time) to 
    # uniquely identify this model run.
    run_ID_number = time.strftime("%Y%m%d-%H%M%S")
    print "\n******************************************************************************"
    print time.strftime("%I:%M:%S %p") + ": started model run number %s."%(run_ID_number)
    print "******************************************************************************\n"

    for t in timesteps:
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

        region.increment_age()
            
        #saved_data.append(copy.deepcopy(region))
        
        num_persons = region.census()

        if num_persons == 0:
            print "End of model run: population is zero."

        print "    Pop: %s\tBirths: %s\tDeaths: %s\tMarr: %s\tMigr: %s"%(
                num_persons, num_births, num_deaths, num_marriages, num_migrations)

    print "\n******************************************************************************"
    print time.strftime("%I:%M:%S %p") + ":  finished model run. Total elapsed time: ", elapsed_time(modelrun_starttime)
    print "******************************************************************************\n"

    return saved_data, run_ID_number

def elapsed_time(start_time):
    elapsed = int(time.time() - start_time)
    hours = elapsed / 3600
    minutes = (elapsed - hours * 3600) / 60
    seconds = elapsed - hours * 3600 - minutes * 60
    return "%ih %im %is" %(hours, minutes, seconds)
