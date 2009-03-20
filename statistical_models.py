"""
Part of Chitwan Valley agent-based model.

Contains statistical models to calulate hazards (such as of birth, and of 
marriage) and run OLS regressions (to calculate land use).

TODO: code the stat models. For now, pre-specified hazard distributions are 
used.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

from chitwanABM import rcParams

model_time_units = rcParams['model.time_units']
hazard_time_units = rcParams['hazard_time_units']

#TODO: these hazards should be derived from the region, not directly from RcParams
birth_hazards = rcParams['hazard_birth']
death_hazards = rcParams['hazard_death']
marriage_hazards = rcParams['hazard_marriage']
migration_hazards = rcParams['hazard_migration']

class UnitsError(Exception):
    pass

def __hazard_index__(t):
    """Matches units of time in model to those the hazard is expressed in. For 
    instance: if hazards are specified for decades, whereas the model runs in 
    months, __hazard_index__ when provided with an age in months, convert it to 
    decades, rounding down. NOTE: all hazards must be expressed with the same 
    time units."""
    if model_time_units == 'months':
        if hazard_time_units == 'months':
            return t
        if hazard_time_units == 'years':
            return int(round((t * 12) / 12.))
        if hazard_time_units == 'decades':
            return int(round((t * 12) / 120.))
    elif model_time_units == 'years':
        if hazard_time_units == 'months':
            raise UnitsError("model_time_units cannot be greater than hazard_time_units")
        if hazard_time_units == 'years':
            return t
        if hazard_time_units == 'decades':
            return int(round(t / 10.))
    elif model_time_units == 'decades':
        if hazard_time_units == 'months':
            raise UnitsError("model_time_units cannot be greater than hazard_time_units")
        if hazard_time_units == 'years':
            raise UnitsError("model_time_units cannot be greater than hazard_time_units")
        if hazard_time_units == 'decades':
            return t
    else:
        raise UnitsError("unhandled model_time_units or hazard_time_units")
def convert_hazard_units(hazard):
    "Convert hazard so units match timestep used in the model."
    # If the hazard time units don't match the model timestep units, then the 
    # hazards need to be converted.
    if model_time_units == 'months':
        if hazard_time_units == 'months':
            return hazard
        if hazard_time_units == 'years':
            return 1 - (1 - hazard)**(1/12.)
        if hazard_time_units == 'decades':
            return 1 - (1 - hazard)**(1/120.)
    elif model_time_units == 'years':
        if hazard_time_units == 'months':
            raise UnitsError("model_time_units cannot be greater than hazard_time_units")
        if hazard_time_units == 'years':
            return hazard
        if hazard_time_units == 'decades':
            return 1 - (1 - hazard)**(1/10.)
    elif model_time_units == 'decades':
        if hazard_time_units == 'months':
            raise UnitsError("model_time_units cannot be greater than hazard_time_units")
        if hazard_time_units == 'years':
            raise UnitsError("model_time_units cannot be greater than hazard_time_units")
        if hazard_time_units == 'decades':
            return hazard
    else:
        raise UnitsError("unhandled model_time_units or hazard_time_units")

#def hazard_birth(person, neighborhood, landuse):
def calc_hazard_birth(person):
    "Calculates the hazard of birth for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    return convert_hazard_units(birth_hazards[hazard_index])

#def hazard_marriage(person, neighborhood, landuse):
def calc_hazard_marriage(person):
    "Calculates the hazard of marriage for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    return convert_hazard_units(marriage_hazards[hazard_index])

def calc_hazard_death(person):
    "Calculates the hazard of death for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    try:
        return convert_hazard_units(death_hazards[hazard_index])
    except:
        raise IndexError("error calculating death hazard (index %s)"%(hazard_index))

def calc_hazard_migration(person):
    "Calculates the hazard of death for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    return convert_hazard_units(migration_hazards[hazard_index])

def calc_landuse(region):
    "Calculates land use based on population parameters and past land use."
    return landuse
