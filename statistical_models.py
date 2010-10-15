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
Contains statistical models to calulate hazards (such as of birth, and of 
marriage) and run OLS regressions (to calculate land use).

TODO: code the stat models. For now, pre-specified hazard distributions are 
used.
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
death_hazards_male = convert_hazard_units(rcParams['hazard.death.male'])
death_hazards_female = convert_hazard_units(rcParams['hazard.death.female'])
marriage_hazards_male = convert_hazard_units(rcParams['hazard.marriage.male'])
marriage_hazards_female = convert_hazard_units(rcParams['hazard.marriage.female'])
migration_hazards_male = convert_hazard_units(rcParams['hazard.migration.male'])
migration_hazards_female = convert_hazard_units(rcParams['hazard.migration.female'])

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
    "Calculates the hazard of migration for an agent."
    age = person.get_age()
    hazard_index = __hazard_index__(age)
    if person.get_sex() == 'female':
        return migration_hazards_female[hazard_index]
    elif person.get_sex() == 'male':
        return migration_hazards_male[hazard_index]

def calc_first_birth_time():
    "Calculates the time from marriage until first birth for this person."
    first_birth_prob_dist = rcParams['prob.firstbirth.times']
    return int(draw_from_prob_dist(first_birth_prob_dist))

def calc_des_num_children():
    "Calculates the desired number of children for this person."
    des_num_children_prob_dist = rcParams['prob.num.children.desired']
    # Use np.floor as the last number in the des_num_children prob dist (10) is 
    # not actually seen in the Chitwan data. It is included only as the 
    # right-hand bound of the distribution.
    return np.floor(draw_from_prob_dist(des_num_children_prob_dist))

def calc_hh_area():
    "Calculates the time from marriage until first birth for this person."
    hh_area_prob_dist = rcParams['lulc.area.hh']
    return draw_from_prob_dist(hh_area_prob_dist)

def draw_from_prob_dist(prob_dist):
    """
    Draws a random number from a manually specified probability distribution,
    where the probability distribution is a tuple specified as:
        ([a, b, c, d], [1, 2, 3])
    where a, b, c, and d are bin limits, and 1, 2, and 3 are the probabilities 
    assigned to each bin. Notice one more bin limit must be specifed than the 
    number of probabilities given (to close the interval).
    """
    # First randomly choose the bin, with the bins chosen according to their 
    # probability.
    binlims, probs = prob_dist
    num = np.random.rand() * np.sum(probs)
    n = 0
    probcumsums = np.cumsum(probs)
    for upprob in probcumsums[1:]:
        if num < upprob:
            break
        n += 1
    upbinlim = binlims[n+1]
    lowbinlim = binlims[n]
    # Now we know the bin lims, so draw a random number evenly distributed 
    # between those two limits.
    return np.random.uniform(lowbinlim, upbinlim)
