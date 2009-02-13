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

class DataStore:
    """A class to store all agents and their attributes for each timestep of 
    the model. Useful for later computing statistics or for debugging the 
    model"""
    def __init__():
        self._landuse = []
        self._region = []

    def add_data(landuse, region):
        self._landuse.append(landuse)
        self._region.append(region)

def mainloop(pop, land):
    """This function contains the main model loop. Passed to it is an instance 
    of the modelRun class, which contains parameters defining the size of each 
    timestep, the person, household, and neighborhood agents to be used in the 
    model, and the landuse parameters."""

    # savedData will store the results of each timestep.
    savedData = DataStore()

    for t in timeSteps()
        people.births()
        people.deaths()
        people.marriages()
        people.increment_age()

        # Calculate and update land use
        land.update(people, time)

        savedData.addData(people, land)
