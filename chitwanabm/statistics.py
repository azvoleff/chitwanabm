# Copyright 2008-2012 Alex Zvoleff
#
# This file is part of the chitwanabm agent-based model.
# 
# chitwanabm is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# chitwanabm is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# chitwanabm.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff (azvoleff@mail.sdsu.edu) in the Department of Geography 
# at San Diego State University with any comments or questions. See the 
# README.txt file for contact information.

"""
Contains statistical models to calculate probabilities (such as of birth, and of 
marriage).
"""

from __future__ import division

import os

import logging

logger = logging.getLogger(__name__)

from chitwanabm import rc_params, np

if not rc_params.is_initialized():
    # Load the rc parameters if this module was imported directly (needed for 
    # Sphinx autodoc).
    rc_params.load_default_params('chitwanabm')
    rc_params.initialize('chitwanabm')
rcParams = rc_params.get_params()

from pyabm import boolean_choice
from pyabm.statistics import convert_probability_units, get_probability_index, \
        draw_from_prob_dist, calc_prob_from_prob_dist, UnitsError, \
        StatisticsError

prob_time_units = rcParams['probability.time_units']

#TODO: these probabilities should be derived from the region, not directly from rcParams
death_probabilities_male = convert_probability_units(rcParams['probability.death.male'], prob_time_units)
death_probabilities_female = convert_probability_units(rcParams['probability.death.female'], prob_time_units)
marriage_probabilities_male = convert_probability_units(rcParams['probability.marriage.male'], prob_time_units)
marriage_probabilities_female = convert_probability_units(rcParams['probability.marriage.female'], prob_time_units)
migration_probabilities_male = convert_probability_units(rcParams['probability.migration.male'], prob_time_units)
migration_probabilities_female = convert_probability_units(rcParams['probability.migration.female'], prob_time_units)

def calc_first_birth_prob_zvoleff(person, time):
    """
    Calculates the probability of a first birth in a given month for an agent, 
    using the results of Zvoleff's empirical analysis, following the analysis 
    of Ghimire and Axinn (2010).
    """
    #########################################################################
    # Intercept
    inner = rcParams['firstbirth.zv.coef.(Intercept)']

    #########################################################################
    # Adult community context
    neighborhood = person.get_parent_agent().get_parent_agent()
    # Convert nbh_area form square meters to square kilometers
    nbh_area = neighborhood._land_total / 1000000
    inner += rcParams['firstbirth.zv.coef.total_t1'] * nbh_area
    percent_agveg = (neighborhood._land_agveg / neighborhood._land_total) * 100
    inner += rcParams['firstbirth.zv.coef.percagveg_t1'] * percent_agveg
    inner += rcParams['firstbirth.zv.coef.dist_nara'] * neighborhood._distnara
    inner += rcParams['firstbirth.zv.coef.elec_avail'] * neighborhood._elec_available
    inner += rcParams['firstbirth.zv.coef.avg_yrs_services_lt15'] * neighborhood._avg_yrs_services_lt15

    #########################################################################
    # Parents characteristics
    inner += rcParams['firstbirth.zv.coef.mother_num_children'] * person.get_mother_num_children()
    inner += rcParams['firstbirth.zv.coef.mother_school'] * person.get_mother_years_schooling()
    inner += rcParams['firstbirth.zv.coef.mother_work'] * person.get_mother_work()
    inner += rcParams['firstbirth.zv.coef.father_school'] * person.get_father_years_schooling()
    inner += rcParams['firstbirth.zv.coef.father_work'] * person.get_father_work()
    inner += rcParams['firstbirth.zv.coef.parents_contracep_ever'] * person._parents_contracep_ever

    #########################################################################
    # Other personal controls
    ethnicity = person.get_ethnicity()
    assert ethnicity!=None, "Ethnicity must be defined"
    if ethnicity == "HighHindu":
        # This was the reference level
        pass
    elif ethnicity == "HillTibeto":
        inner += rcParams['firstbirth.zv.coef.ethnicHillTibeto']
    elif ethnicity == "LowHindu":
        inner += rcParams['firstbirth.zv.coef.ethnicLowHindu']
    elif ethnicity == "Newar":
        inner += rcParams['firstbirth.zv.coef.ethnicNewar']
    elif ethnicity == "TeraiTibeto":
        inner += rcParams['firstbirth.zv.coef.ethnicTeraiTibeto']

    inner += rcParams['firstbirth.zv.coef.age_at_first_marr'] * person.get_marriage_age_years(time)
    #inner += rcParams['firstbirth.zv.coef.mths_marr_pre_1997']
 
    #########################################################################
    # Hazard duration
    marriage_time = time - person._marriage_time
    if marriage_time <= 6:
        inner += rcParams['firstbirth.zv.coef.marr_duration[0,6)']
    elif marriage_time <= 12:
        inner += rcParams['firstbirth.zv.coef.marr_duration[6,12)']
    elif marriage_time <= 18:
        inner += rcParams['firstbirth.zv.coef.marr_duration[12,18)']
    elif marriage_time <= 24:
        inner += rcParams['firstbirth.zv.coef.marr_duration[18,24)']
    elif marriage_time <= 30:
        inner += rcParams['firstbirth.zv.coef.marr_duration[24,30)']
    elif marriage_time <= 36:
        inner += rcParams['firstbirth.zv.coef.marr_duration[30,36)']
    elif marriage_time > 36:
        inner += rcParams['firstbirth.zv.coef.marr_duration[36,42)']

    #########################################################################
    # Education level of individual
    assert person._schooling !=None, "schoolinging must be defined"
    if person._schooling < 4:
        # This was the reference level
        pass
    elif person._schooling < 8:
        inner += rcParams['firstbirth.zv.coef.schooling_yrs_cat[4,7)']
    elif person._schooling < 11:
        inner += rcParams['firstbirth.zv.coef.schooling_yrs_cat[7,11)']
    elif person._schooling >= 11:
        inner += rcParams['firstbirth.zv.coef.schooling_yrs_cat[11,99)']

    prob = 1./(1 + np.exp(-inner))
    if rcParams['log_stats_probabilities']:
        logger.debug("Person %s first birth probability %.6f (marriage_time: %s)"%(person.get_ID(), prob,  person._marriage_time))
    return prob

def calc_probability_marriage_zvoleff(person, time):
    """
    Calculates the probability of marriage for an agent, using the results of 
    Alex Zvoleff's empirical analysis of the CVFS data, following the results 
    of the analysis conducted by Yabiku (2006).
    """
    inner = rcParams['marrtime.zv.coef.(Intercept)']

    ethnicity = person.get_ethnicity()
    assert ethnicity!=None, "Ethnicity must be defined"
    if ethnicity == "HighHindu":
        # This was the reference level
        pass
    elif ethnicity == "HillTibeto":
        inner += rcParams['marrtime.zv.coef.ethnicHillTibeto']
    elif ethnicity == "LowHindu":
        inner += rcParams['marrtime.zv.coef.ethnicLowHindu']
    elif ethnicity == "Newar":
        inner += rcParams['marrtime.zv.coef.ethnicNewar']
    elif ethnicity == "TeraiTibeto":
        inner += rcParams['marrtime.zv.coef.ethnicTeraiTibeto']

    # Gender
    if person.get_sex() == "female":
        inner += rcParams['marrtime.zv.coef.genderfemale']

    age = person.get_age_years()
    inner += rcParams['marrtime.zv.coef.age'] * age
    inner += rcParams['marrtime.zv.coef.I(age^2)'] * (age ** 2)

    # Neighborhood characteristics
    neighborhood = person.get_parent_agent().get_parent_agent()
    log_percent_agveg = np.log((neighborhood._land_agveg / neighborhood._land_total)*100 + 1)
    inner += rcParams['marrtime.zv.coef.interp_logpercagveg'] * log_percent_agveg

    inner += rcParams['marrtime.zv.coef.SCHLFT_1996'] * neighborhood._school_min_ft
    inner += rcParams['marrtime.zv.coef.HLTHFT_1996'] * neighborhood._health_min_ft
    inner += rcParams['marrtime.zv.coef.BUSFT_1996'] * neighborhood._bus_min_ft
    inner += rcParams['marrtime.zv.coef.MARFT_1996'] * neighborhood._market_min_ft
    inner += rcParams['marrtime.zv.coef.EMPFT_1996'] * neighborhood._employer_min_ft

    # Schooling
    inner += rcParams['marrtime.zv.coef.schooling_yrs'] * neighborhood._school_min_ft
    if person.is_in_school():
        inner += rcParams['marrtime.zv.coef.in_school_1996']

    # Account for monthly differences in marriage rates - some days (and 
    # months) are more auspicious for marriage than others.
    month_num = int(np.mod(np.round(time*12, 0), 12) + 1)
    if month_num == 1:
        # This was the reference level
        pass
    elif month_num == 2:
        inner += rcParams['marrtime.zv.coef.month2']
    elif month_num == 3:
        inner += rcParams['marrtime.zv.coef.month3']
    elif month_num == 4:
        inner += rcParams['marrtime.zv.coef.month4']
    elif month_num == 5:
        inner += rcParams['marrtime.zv.coef.month5']
    elif month_num == 6:
        inner += rcParams['marrtime.zv.coef.month6']
    elif month_num == 7:
        inner += rcParams['marrtime.zv.coef.month7']
    elif month_num == 8:
        inner += rcParams['marrtime.zv.coef.month8']
    elif month_num == 9:
        inner += rcParams['marrtime.zv.coef.month9']
    elif month_num == 10:
        inner += rcParams['marrtime.zv.coef.month10']
    elif month_num == 11:
        inner += rcParams['marrtime.zv.coef.month11']
    elif month_num == 12:
        inner += rcParams['marrtime.zv.coef.month12']
    
    prob = 1./(1 + np.exp(-inner))
    if rcParams['log_stats_probabilities']:
        logger.debug("Person %s marriage probability %.6f (age: %s)"%(person.get_ID(), prob, person.get_age_years()))
    return prob

def calc_probability_marriage_simple(person):
    """
    Calculate the probability of marriage using a simple sex and age dependent 
    probability distribution.
    """
    age = person.get_age_months()
    probability_index = get_probability_index(age, prob_time_units)
    if person.get_sex() == 'female':
        return marriage_probabilities_female[probability_index]
    elif person.get_sex() == 'male':
        return marriage_probabilities_male[probability_index]

def calc_probability_divorce(person):
    "Calculates the probability of death for an agent."
    #TODO: Complete this function to take into account logistic regression results.
    return boolean_choice(rcParams['prob.marriage.divorce'])

def choose_spouse(person, eligible_mates):
    """
    Once lists of marrying men and women are created, this function chooses a 
    wife for a particular male based on the age differential between the man 
    and each woman, based on observed data.
    """
    sp_probs = []
    for eligible_mate in eligible_mates:
        if person.get_sex == "male":
            agediff = person.get_age_years() - eligible_mate.get_age_years()
        else:
            agediff = eligible_mate.get_age_years() - person.get_age_years()
        if person.get_sex() == eligible_mate.get_sex() or \
                person.get_ethnicity() != eligible_mate.get_ethnicity() or \
                person.is_sibling(eligible_mate):
            sp_probs.append(0)
        else:
            sp_probs.append(calc_prob_from_prob_dist(rcParams['spousechoice.male.agediff'], agediff))
        #print "f", eligible_mate.get_age_years(),
        #print "m", male.get_age_years(), "|",
    if sum(sp_probs) == 0:
        # In this case NONE of the eligible_mates are eligible (all of different
        # ethnicities than the person).
        return None
    num = np.random.rand() * np.sum(sp_probs)
    sp_probs = np.cumsum(sp_probs)
    n = 0
    for problim in sp_probs[0:-1]:
        if num <= problim:
            break
        n += 1
    return eligible_mates[n]

def calc_spouse_age_diff(person):
    """
    This function draws the age difference between this person and their 
    spouse based on the observed probability distribution. Note that the age 
    difference is defined as male's age - woman's age, so positive age 
    differences should be subtracted from men's ages to get their spouse age, and 
    added to women's.
    """
    return draw_from_prob_dist(rcParams['spousechoice.male.agediff'])

def calc_probability_death(person):
    "Calculates the probability of death for an agent."
    age = person.get_age_months()
    probability_index = get_probability_index(age, prob_time_units)
    try:
        if person.get_sex() == 'female':
            return death_probabilities_female[probability_index]
        elif person.get_sex() == 'male':
            return death_probabilities_male[probability_index]
    except IndexError:
        raise IndexError("error calculating death probability (index %s)"%(probability_index))

def calc_probability_migration_simple(person):
    "Calculates the probability of migration for an agent."
    age = person.get_age_months()
    probability_index = get_probability_index(age, prob_time_units)
    if person.get_sex() == 'female':
        return migration_probabilities_female[probability_index]
    elif person.get_sex() == 'male':
        return migration_probabilities_male[probability_index]

def calc_probability_migration_zvoleff(person):
    """
    Calculates the probability of local-distant migration for an agent, using 
    the results of Alex Zvoleff's empirical analysis of the CVFS data, 
    following the results of the analysis conducted by Massey et al. (2010).
    """
    #########################################################################
    # Intercept
    inner = rcParams['migration.zv.coef.intercept']

    if person.is_in_school():
        inner += rcParams['migration.zv.coef.in_school']

    inner += person.get_years_schooling() * rcParams['migration.zv.coef.years_schooling']

    #######################################################################
    # Household level variables
    household = person.get_parent_agent()
    inner += rcParams['migration.zv.coef.own_farmland'] * household._own_land

    #######################################################################
    # Neighborhood level variables
    neighborhood = household.get_parent_agent()
    inner += rcParams['migration.zv.coef.log_market_min_ft'] * np.log(neighborhood._market_min_ft + 1)

    #########################################################################
    # Other controls
    if person.get_sex() == "female":
        inner += rcParams['migration.zv.coef.female']

    ethnicity = person.get_ethnicity()
    assert ethnicity!=None, "Ethnicity must be defined"
    if ethnicity == "HighHindu":
        # This was the reference level
        pass
    elif ethnicity == "HillTibeto":
        inner += rcParams['migration.zv.coef.ethnicHillTibeto']
    elif ethnicity == "LowHindu":
        inner += rcParams['migration.zv.coef.ethnicLowHindu']
    elif ethnicity == "Newar":
        inner += rcParams['migration.zv.coef.ethnicNewar']
    elif ethnicity == "TeraiTibeto":
        inner += rcParams['migration.zv.coef.ethnicTeraiTibeto']

    age = person.get_age_years()
    if (age >= 15) & (age <= 24):
        inner += rcParams['migration.zv.coef.age15-24']
    elif (age > 24) & (age <= 34):
        inner += rcParams['migration.zv.coef.age24-34']
    elif (age > 34) & (age <= 44):
        inner += rcParams['migration.zv.coef.age34-44']
    elif (age > 44) & (age <= 55):
        inner += rcParams['migration.zv.coef.age45-55']
    elif (age > 55):
        # Reference class
        pass

    prob = 1./(1 + np.exp(-inner))
    if rcParams['log_stats_probabilities']:
        logger.debug("Person %s migration probability %.6f (age: %s)"%(person.get_ID(), prob, person.get_age_years()))
    return prob

def calc_migration_length(person, BURN_IN):
    """
    Calculated the length of a migration from a probability distribution.

    Note: The BURN_IN variable is used in the initialization of a model run to 
    model migrations that occurred prior to the beginning of the data 
    collection. Permanent migrations are not allowed during this burn-in 
    period.
    """
    # First decide if it is permanent, according to the 
    # "prob.migration.length.permanent" parameter:
    if not BURN_IN and np.random.rand() < rcParams['prob.migration.length.permanent']:
        # TODO: Instead of very long term in agent-store, just remove them from 
        # the model with the make_permanent_outmigration method.
        return 99999999
    mig_length_prob_dist = rcParams['prob.migration.lengths']
    # Use ceil here so the minimum value is 1, and the maximum value is 36
    return np.ceil(draw_from_prob_dist(mig_length_prob_dist))

def calc_num_inmigrant_households():
    """
    Draws the number of in migrating households in a given month based on an 
    empirical probability distribution.
    """
    return int(draw_from_prob_dist(rcParams['inmigrant_HH.prob.num_HHs']))

def calc_inmigrant_household_ethnicity(as_integer=False):
    ethnicity = int(draw_from_prob_dist(rcParams['inmigrant_HH.prob.ethnicity']))
    if not as_integer:
        if ethnicity == 1:
            ethnicity = "HighHindu"
        elif ethnicity == 2:
            ethnicity = "HillTibeto"
        elif ethnicity == 3:
            ethnicity = "LowHindu"
        elif ethnicity == 4:
            ethnicity = "Newar"
        elif ethnicity == 5:
            ethnicity = "TeraiTibeto"
        else:
            logger.critical("Undefined ethnicity %s drawn for new inmigrant household"%ethnicity)
    return ethnicity

def calc_inmigrant_household_size():
    return int(draw_from_prob_dist(rcParams['inmigrant_HH.prob.hh_size']))

def calc_probability_HH_outmigration(household, timestep):
    """
    Draws the number of out migrating households in a given month based on an 
    empirical probability distribution.
    """
    outmigrant_HH_prob = rcParams['outmigrant_HH.prob']
    return outmigrant_HH_prob

def calc_first_birth_time(person):
    """
    Calculates the time from marriage until first birth for this person (not 
    used if the Ghimire and Axinn 2010 model is selected in rcparams.
    """
    first_birth_prob_dist = rcParams['prob.firstbirth.times']
    return int(draw_from_prob_dist(first_birth_prob_dist))

def calc_des_num_children():
    "Calculates the desired number of children for this person."
    des_num_children_prob_dist = rcParams['prob.num.children.desired']
    # Use np.floor as the last number in the des_num_children prob dist (10) is 
    # not actually seen in the Chitwan data. It is included only as the 
    # right-hand bound of the distribution.
    return np.floor(draw_from_prob_dist(des_num_children_prob_dist))

def calc_birth_interval():
    "Calculates the birth interval for this person."
    birth_interval_prob_dist = rcParams['prob.birth.intervals']
    return np.floor(draw_from_prob_dist(birth_interval_prob_dist ))

def calc_hh_area():
    "Calculates the area of this household."
    hh_area_prob_dist = rcParams['lulc.area.hh']
    return draw_from_prob_dist(hh_area_prob_dist)

def calc_fuelwood_usage_probability(household, time):
    """
    Calculates the probability of fuelwood usage (not quantity of usage, but 
    probability of using any wood at all) at the household-level.
    """

    hhsize = household.num_members()
    if hhsize == 0:
        # Households may be empty but still in the model if they have 
        # out-migrants currently away, but that will be returning.
        return 0

    inner = rcParams['fw_usageprob.coef.intercept']

    ######################################################################
    # Household level vars
    inner += rcParams['fw_usageprob.coef.hhsize'] * hhsize

    hh_ethnicity = household.get_hh_head().get_ethnicity()
    if hh_ethnicity == "HighHindu":
        # This was the reference class
        pass
    elif hh_ethnicity == "LowHindu":
        inner += rcParams['fw_usageprob.coef.ethnicLowHindu']
    elif hh_ethnicity == "Newar":
        inner += rcParams['fw_usageprob.coef.ethnicNewar']
    elif hh_ethnicity == "HillTibeto":
        inner += rcParams['fw_usageprob.coef.ethnicHillTibeto']
    elif hh_ethnicity == "TeraiTibeto":
        inner += rcParams['fw_usageprob.coef.ethnicTeraiTibeto']
    else:
        raise StatisticsError("No coefficient was specified for ethnicity '%s'"%hh_ethnicity)

    inner += rcParams['fw_usageprob.coef.meangender'] * household.mean_gender()

    ######################################################################
    # Neighborhood level vars
    neighborhood = household.get_parent_agent()
    inner += rcParams['fw_usageprob.coef.elecavail'] * \
            neighborhood._elec_available
    inner += rcParams['fw_usageprob.coef.distnara_km'] * \
            neighborhood._distnara
    if neighborhood._forest_closest_type == "BZ":
        # Reference level
        pass
    elif neighborhood._forest_closest_type == "CNP":
        inner += rcParams['fw_usageprob.coef.closest_typeCNP']
    else:
        raise StatisticsError("No coefficient was specified for closest forest type '%s'"%neighborhood._forest_closest_type)

    prob = 1./(1 + np.exp(-inner))
    if rcParams['log_stats_probabilities']:
        logger.debug("Household %s fuelwood usage probability %.6f (size: %s)"%(household.get_ID(), prob, household.num_members()))
    return prob


def calc_daily_fuelwood_usage_simple(household, time):
    """
    Calculates household-level fuelwood usage, using the results of a 2009 
    survey of fuelwood usage in the valley.
    """
    hhsize = household.num_members()
    if hhsize == 0:
        return 0
    wood_usage = rcParams['fw_demand.simple.coef.intercept']
    if hhsize >= 6:
        # Hold household size constant after 6 persons hhsize since model is 
        # unstable after 6
        wood_usage += rcParams['fw_demand.simple.coef.hhsize'] * 6
        wood_usage += rcParams['fw_demand.simple.coef.hhsize_squared'] * 6
    else:
        wood_usage += rcParams['fw_demand.simple.coef.hhsize'] * hhsize
        wood_usage += rcParams['fw_demand.simple.coef.hhsize_squared'] * hhsize
    wood_usage += rcParams['fw_demand.simple.coef.hhsize'] * hhsize
    wood_usage += rcParams['fw_demand.simple.coef.hhsize_squared'] * hhsize
    if household.get_hh_head().get_ethnicity() == "HighHindu":
        wood_usage += rcParams['fw_demand.simple.coef.upper_caste_hindu']
    wood_usage += household.any_non_wood_fuel() * rcParams['fw_demand.simple.coef.own_non_wood_stove']
    wood_usage += np.random.randn()*np.sqrt(rcParams['fw_demand.simple.residvariance'])
    if wood_usage < 0:
        # Account for less than zero wood usage (could occur due to the random 
        # number added above to account for the low percent variance explained 
        # by the model).
        wood_usage = 0
    # The prediction is per person - multiply it by hhsize to get total 
    # household fuelwood consumption:
    wood_usage = wood_usage * hhsize
    return wood_usage

def calc_daily_fuelwood_usage_migration_feedback(household, time):
    """
    Calculates household-level fuelwood usage, using the results of a 2009 
    survey of fuelwood usage in the valley.
    """
    hhsize = household.num_members()
    if hhsize == 0:
        return 0
    wood_usage = rcParams['fw_demand.migfeedback.coef.intercept']
    if hhsize >= 6:
        # Hold household size constant after 6 persons hhsize since model is 
        # unstable after 6
        wood_usage += rcParams['fw_demand.migfeedback.coef.hhsize'] * 6
        wood_usage += rcParams['fw_demand.migfeedback.coef.hhsize_squared'] * 6
    else:
        wood_usage += rcParams['fw_demand.migfeedback.coef.hhsize'] * hhsize
        wood_usage += rcParams['fw_demand.migfeedback.coef.hhsize_squared'] * hhsize
    if household.get_hh_head().get_ethnicity() == "HighHindu":
        wood_usage += rcParams['fw_demand.migfeedback.coef.upper_caste_hindu']
    wood_usage += household.any_non_wood_fuel() * rcParams['fw_demand.migfeedback.coef.own_non_wood_stove']
    wood_usage += np.random.randn()*np.sqrt(rcParams['fw_demand.migfeedback.residvariance'])
    if household._lastmigrant_time > (time - 1):
        wood_usage += rcParams['fw_demand.migfeedback.coef.anyLDmigr']
    if wood_usage < 0:
        # Account for less than zero wood usage (could occur due to the random 
        # number added above to account for the low percent variance explained 
        # by the model).
        wood_usage = 0
    # The prediction is per person - multiply it by hhsize to get total 
    # household fuelwood consumption:
    wood_usage = wood_usage * hhsize
    return wood_usage

def calc_education_level(person):
    """
    Calculate education level for person, based on results of empirical analysis of CVFS panel data.
    """
    levels = rcParams['education.depvar_levels']

    prob_y_gte_j = np.zeros(len(levels) - 1) # probability y >= j
    for n in np.arange(len(prob_y_gte_j)):
        intercept = rcParams['education.coef.intercepts'][n]
        xb_sum = 0

        # Individual-level characteristics
        if person.get_sex() == "female":
            xb_sum += rcParams['education.coef.female']

        if person.get_ethnicity() == "HighHindu":
            # This was the reference class
            pass
        elif person.get_ethnicity() == "LowHindu":
            xb_sum += rcParams['education.coef.ethnicLowHindu']
        elif person.get_ethnicity() == "Newar":
            xb_sum += rcParams['education.coef.ethnicNewar']
        elif person.get_ethnicity() == "HillTibeto":
            xb_sum += rcParams['education.coef.ethnicHillTibeto']
        elif person.get_ethnicity() == "TeraiTibeto":
            xb_sum += rcParams['education.coef.ethnicTeraiTibeto']
        else:
            raise StatisticsError("No coefficient was specified for ethnicity '%s'"%person.get_ethnicity())

        # Neighborhood-level characteristics
        neighborhood = person.get_parent_agent().get_parent_agent()
        xb_sum += rcParams['education.coef.avg_yrs_services_lt15'] * \
                neighborhood._avg_yrs_services_lt15

        prob_y_gte_j[n] = 1. / (1 + np.exp(-(intercept + xb_sum)))

    prob_y_eq_j = np.zeros(4) # probability y == j
    prob_y_eq_j[0] = 1 - prob_y_gte_j[0]
    # Loop over all but the first cell of prob_y_eq_j
    for j in np.arange(1, len(prob_y_gte_j)):
        prob_y_lt_j = np.sum(prob_y_eq_j[0:j])
        prob_y_eq_j[j] = 1 - prob_y_gte_j[j] - prob_y_lt_j
    prob_cutoffs = np.cumsum(prob_y_eq_j)
    prob_cutoffs[-1]  = 1

    # Code for testing only:
    #print prob_cutoffs

    rand = np.random.rand()
    for n in np.arange(len(prob_cutoffs)):
        if rand <= prob_cutoffs[n]:
            return levels[n]
    # Should never reach the next line.
    raise StatisticsError("Check level calculation - no class predicted")
