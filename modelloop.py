"""
Part of Chitwan Valley agent-based model.

Contains main model loop: Contains the main loop for the model. Takes input 
parameters read from runModel.py, and passes results of model run back.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

from chitwanABM import rcParams

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

timezero = rcParams['model.timezero']
endtime = rcParams['model.endtime']
timestep= rcParams['model.timestep']
timesteps = np.arange(timezero, endtime, timestep)

def mainloop(regions):
    """This function contains the main model loop. Passed to it is an instance 
    of the modelRun class, which contains parameters defining the size of each 
    timestep, the person, household, and neighborhood agents to be used in the 
    model, and the landuse parameters."""

    # savedData will store the results of each timestep.
    savedData = DataStore()

    for t in timeSteps()
        for region in regions():
            region.births()
            region.deaths()
            region.marriages()
            region.increment_age()

            # Calculate and update land use
            land.update(region, time)

            savedData.addData(region)
