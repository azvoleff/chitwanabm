"""
Part of Chitwan Valley agent-based model.

Contains main model loop: Contains the main loop for the model. Takes input 
parameters read from runModel.py, and passes results of model run back.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

def main(modelRun):
    """This function contains the main model loop. Passed to it is an instance 
    of the modelRun class, which contains parameters defining the size of each 
    timestep, the person, household, and neighborhood agents to be used in the 
    model, and the landuse parameters."""

    for t in modelRun.timeSteps()

        for person in modelRun.persons():
            # Mortality
            person.Survive()

            # Marriages

        # Calculate and update land use

