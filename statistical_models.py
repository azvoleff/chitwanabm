"""
Part of Chitwan Valley agent-based model.

Contains statistical models to calulate hazards (such as of birth, and of 
marriage) and run OLS regressions (to calculate land use).

TODO: code the stat models. For now, pre-specified hazard distributions are 
used.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

from ChitwanABM import rcParams

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

hazard_time_units = rcParams['hazard.time_units']

class UnitsError(Exception):
    pass

def convert_hazard_units(hazard):
    """
    Converts hazard so units match timestep used in the model, assuming hazard 
    function is uniform across the interval.

    Conversions are made accordingly using conditional probability.
    """
    # If the hazard time units don't match the model timestep units, then the 
    # hazards need to be converted.
    if hazard_time_units == 'months':
        pass
    elif hazard_time_units == 'years':
        for key, value in hazard.iteritems():
            hazard[key] = 1 - (1 - value)**(1/12.)
    elif hazard_time_units == 'decades':
        for key, value in hazard.iteritems():
            hazard[key] = 1 - (1 - value)**(1/120.)
    else:
        raise UnitsError("unhandled hazard_time_units")
    return hazard

#TODO: these hazards should be derived from the region, not directly from rcParams
birth_hazards = convert_hazard_units(rcParams['hazard.birth'])
death_hazards_male = convert_hazard_units(rcParams['hazard.death.male'])
death_hazards_female = convert_hazard_units(rcParams['hazard.death.female'])
marriage_hazards_male = convert_hazard_units(rcParams['hazard.marriage.male'])
marriage_hazards_female = convert_hazard_units(rcParams['hazard.marriage.female'])
migration_hazards = convert_hazard_units(rcParams['hazard.migration'])

def __hazard_index__(t):
    """
    Matches units of time in model to those the hazard is expressed in. For 
    instance: if hazards are specified for decades, whereas the model runs in 
    months, __hazard_index__, when provided with an age in months, will convert 
    it to decades, rounding down. NOTE: all hazards must be expressed with the 
    same time units.
    """
    if hazard_time_units == 'months':
        return t
    elif hazard_time_units == 'years':
        return int(round(t / 12.))
    elif hazard_time_units == 'decades':
        return int(round(t / 120.))
    else:
        raise UnitsError("unhandled hazard_time_units")

#def hazard_birth(person, neighborhood, landuse):
def calc_hazard_birth(person):
    "Calculates the hazard of birth for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    #hazard_multiplier = 1 + (person.get_parent_agent().num_members()/30.)
    #hazard_multiplier = 1 - (person.get_parent_agent().num_members()/25.)
    hazard_multiplier = 1
    return hazard_multiplier * birth_hazards[hazard_index]

#def hazard_marriage(person, neighborhood, landuse):
def calc_hazard_marriage(person):
    "Calculates the hazard of marriage for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    if person.get_sex() == 'female':
        return marriage_hazards_female[hazard_index]
    elif person.get_sex() == 'male':
        return marriage_hazards_male[hazard_index]

def calc_hazard_death(person):
    "Calculates the hazard of death for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    try:
        if person.get_sex() == 'female':
            return death_hazards_female[hazard_index]
        elif person.get_sex() == 'male':
            return death_hazards_male[hazard_index]
    except IndexError:
        raise IndexError("error calculating death hazard (index %s)"%(hazard_index))

def calc_hazard_migration(person):
    "Calculates the hazard of death for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    return migration_hazards[hazard_index]

def calc_landuse(region):
    "Calculates land use based on population parameters and past land use."
    # TODO: finish coding this function.
    return landuse
