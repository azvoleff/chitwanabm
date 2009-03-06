"""
Part of Chitwan Valley agent-based model.

Contains statistical models to calulate hazards (such as of birth, and of 
marriage) and run OLS regressions (to calculate land use).

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

model_time_units= rcParams['model.time_units']
hazard_time_units= rcParams['hazard_time_units']

def hazard_birth(person, neighborhood, landuse):
    "Calculates the hazard of .birth for an agent."
    if model_time_units == 'years' and hazard_time_units == 'months':

    else:

    return hazard

def hazard_marriage(person, neighborhood, landuse):
    "Calculates the hazard of marriage for an agent."

    return hazard

def calc_landuse(region):
    "Calculates land use based on population parameters and past land use."

    return landuse
