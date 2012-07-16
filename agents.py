# Copyright 2008-2012 Alex Zvoleff
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
Contains the classes for Person, Household, Neighborhood, and Region agents. 
Person agents are subclasses of the Agent class, while Household, Neighborhood, 
and Region agents are all subclasses of the Agent_set object.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import os
import csv

import numpy as np

from PyABM import IDGenerator, boolean_choice
from PyABM.agents import Agent, Agent_set, Agent_Store

from ChitwanABM import rcParams, random_state
from ChitwanABM.statistics import calc_probability_death, \
        calc_probability_migration_simple, calc_first_birth_time, \
        calc_birth_interval, calc_hh_area, calc_des_num_children, \
        calc_firstbirth_prob_ghimireaxinn2010, calc_fuelwood_usage_simple, \
        calc_probability_migration_masseyetal_2010, calc_migration_length, \
        calc_fuelwood_usage_migration_feedback, calc_education_level, \
        choose_spouse

if rcParams['model.parameterization.marriage'] == 'simple':
    from ChitwanABM.statistics import calc_probability_marriage_simple as calc_probability_marriage
elif rcParams['model.parameterization.marriage'] == 'yabiku2006':
    from ChitwanABM.statistics import calc_probability_marriage_yabiku2006 as calc_probability_marriage
elif rcParams['model.parameterization.marriage'] == 'zvoleff':
    from ChitwanABM.statistics import calc_probability_marriage_zvoleff as calc_probability_marriage
else:
    raise Exception("Unknown option for marriage parameterization: '%s'"%rcParams['model.parameterization.marriage'])

if rcParams['model.parameterization.migration'] == 'simple':
    from ChitwanABM.statistics import calc_probability_migration_simple as calc_probability_migration
elif rcParams['model.parameterization.migration'] == 'massey2010':
    from ChitwanABM.statistics import calc_probability_migration_masseyetal_2010 as calc_probability_migration
else:
    raise Exception("Unknown option for migration parameterization: '%s'"%rcParams['model.parameterization.migration'])

if rcParams['model.parameterization.fuelwood_usage'] == 'simple':
    from ChitwanABM.statistics import calc_fuelwood_usage_simple as calc_fuelwood_usage
elif rcParams['model.parameterization.fuelwood_usage'] == 'migrationfeedback':
    from ChitwanABM.statistics import calc_fuelwood_usage_migration_feedback as calc_fuelwood_usage
else:
    raise Exception("Unknown option for fuelwood usage: '%s'"%rcParams['model.parameterization.fuelwood_usage'])

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

class Person(Agent):
    "Represents a single person agent"
    def __init__(self, world, birthdate, PID=None, mother=None, father=None,
            age=0, sex=None, initial_agent=False, ethnicity=None):
        Agent.__init__(self, world, PID, initial_agent)

        # birthdate is the timestep of the birth of the agent. It is used to 
        # calculate the age of the agent. Agents have a birthdate of 0 if they 
        # were BORN in the first timestep of the model.  If they were used to 
        # initialize the model their birthdates will be negative.
        self._birthdate = birthdate

        # deathdate is used for tracking agent deaths in the results, mainly 
        # for debugging.
        self._deathdate = None
        self._alive = True

        # self._initial_agent is set to "True" for agents that were used to 
        # initialize the model.
        self._initial_agent = initial_agent

        # self._age is used as a convenience to avoid the need to calculate the 
        # agent's age from self._birthdate each time it is needed. It is         
        # important to remember though that all agent's ages must be 
        # incremented with each model timestep, and are expressed in months.
        # The age starts at 0 (it is zero for the entire first timestep of the 
        # model).
        self._age = age

        # Also need to store information on the agent's parents. For agents 
        # used to initialize the model both parent fields are set to "None"
        if father == None:
            self._father = None
        else:
            self._father = father

        if mother == None:
            self._mother = None
        else:
            self._mother = mother

        if sex==None:
            # Person agents are randomly assigned a sex
            if boolean_choice():
                self._sex = 'female'
            else:
                self._sex = 'male'
        elif sex in ['male', 'female']:
            self._sex = sex
        else:
            raise ValueError("%s is not a valid gender"%(sex))

        # The agent's ethnicity in the CVFS data as 1: High Caste Hindu, 2: 
        # Hill Tibetoburmese, 3: Low Caste Hindu, 4: Newar, 5: Terai 
        # Tibetoburmese, 6: Other. Other is dropped from the model for 
        # consistency of published works. Here ethnicity is converted to a 
        # textual representation for clarity (see the preprocessing code).
        self._ethnicity = ethnicity

        # If not defined at birth, self._des_num_children will be defined (for 
        # women) at marriage in the "marry" function.
        self._des_num_children = None

        if self._sex=="female":
            self._birth_interval = calc_birth_interval()

        self._spouse = None

        self._children = []

        if self._sex == "female":
            self._first_birth_timing = calc_first_birth_time(self)
        else:
            self._first_birth_timing = None

        self._marriage_time = None

        self._schooling = 0
        self._final_schooling_level = None
        self._school_status = "undetermined"

        self._work = boolean_choice(.1)
        self._parents_contracep_ever = boolean_choice()

        self._child_school_1hr = boolean_choice()
        self._child_health_1hr = boolean_choice()
        self._child_bus_1hr = boolean_choice()
        self._child_emp_1hr = boolean_choice()

        self._father_work = boolean_choice()
        self._father_school = boolean_choice()
        self._mother_work = boolean_choice()
        self._mother_school = boolean_choice()
        self._mother_num_children = boolean_choice()

    def get_mother(self):
        return self._mother

    def get_num_children(self):
        return len(self._children)

    def get_father(self):
        return self._father

    def get_sex(self):
        return self._sex

    def get_age(self):
        return self._age

    def get_ethnicity(self):
        return self._ethnicity

    def get_spouse(self):
        return self._spouse

    def is_initial_agent(self):
        return self._initial_agent

    def kill(self, time):
        self._alive = False
        self._deathdate = time
        if self.is_married():
            self.divorce()
        household = self.get_parent_agent()
        household.remove_agent(self)

    def marry(self, spouse, time):
        "Marries this agent to another Person instance."
        self._spouse = spouse
        spouse._spouse = self
        # Also assign first birth timing and desired number of children to the 
        # female (if not already defined, which it will be for initial agents).
        if self.get_sex()=="female":
            female=self
        else:
            female=spouse
        if female._des_num_children == None:
            female._des_num_children = calc_des_num_children(self)
        self._marriage_time = time
        spouse._marriage_time = time

    def divorce(self):
        spouse = self._spouse
        spouse._spouse = None
        self._spouse = None

    def is_eligible_for_birth(self, time):
        """
        Check birth timing using Ghimire and Axinn, 2010 first birth timing 
        results or simple probability distribution for first birth timing, 
        depending on the choice of rcparams.
        """
        # Check that the woman has been married long_enough (first birth time), 
        # didn't already give birth more recently than the minimum birth 
        # interval and does not already have greater than their desired family 
        # size.  Note that des_num_children=-1 means no preference ("god's 
        # will").
        if (not (self.get_sex() == 'female')) or (not self.is_married()):
            return False

        if self._age > (rcParams['birth.max_age.years'] * 12):
            return False

        # Handle first births using the appropriate first birth timing 
        # parameterization:
        num_children = len(self._children)
        if (num_children) == 0:
            if self._marriage_time < 1995 and random_state.rand() < .8:
                # Prevent excessive first births at beginning of the model.
                return False
            if rcParams['model.parameterization.firstbirthtiming'] == 'simple':
                if (time - self._marriage_time) >= self._first_birth_timing/12.:
                    return True
                else:
                    return False
            elif rcParams['model.parameterization.firstbirthtiming'] == 'ghimireaxinn2010':
                if (random_state.rand() < calc_firstbirth_prob_ghimireaxinn2010(self, time)):
                    return True
                else:
                    return False
            else:
                raise Exception("Unknown option for first birth timing parameterization: '%s'"%rcParams['model.parameterization.firstbirthtiming'])
        else:
            # Handle births to mothers who have already given birth in the 
            # past:
            if self._last_birth_time >= (time - self._birth_interval/12.):
                return False
            elif (num_children < self._des_num_children) or (self._des_num_children==-1):
                # self._des_num_children = -1 means no preference
                return True
            else:
                return False

    def give_birth(self, time, father):
        "Agent gives birth. New agent inherits characterists of parents."
        assert self.get_sex() == 'female', "Men can't give birth"
        assert self.get_spouse().get_ID() == father.get_ID(), "All births must be in marriages"
        assert self.get_ID() != father.get_ID(), "No immaculate conception (agent: %s)"%(self.get_ID())
        baby = self._world.new_person(birthdate=time, mother=self, father=father, ethnicity=self.get_ethnicity())

        neighborhood = self.get_parent_agent().get_parent_agent()
        ###########################################
        # Set childhood community context for baby:
        # School within 1 hour walk as child:
        if neighborhood._nfo_schl_minft_1996 < 60:
            baby._child_school_1hr = 1
        else:
            baby._child_school_1hr = 0
        # Health center within 1 hour walk as child:
        if neighborhood._nfo_hlth_minft_1996 < 60:
            baby._child_health_1hr = 1
        else:
            baby._child_health_1hr = 0
        # Bus within 1 hour walk as child:
        if neighborhood._nfo_bus_minft_1996 < 60:
            baby._child_bus_1hr = 1
        else:
            baby._child_bus_1hr = 0
        # Market within 1 hour walk as child:
        if neighborhood._nfo_mar_minft_1996 < 60:
            baby._child_mar_1hr = 1
        else:
            baby._child_mar_1hr = 0
        # Employer within 1 hour walk as child:
        if neighborhood._nfo_emp_minft_1996 < 60:
            baby._child_emp_1hr = 1
        else:
            baby._child_emp_1hr = 0

        self._last_birth_time = time
        # Assign a new birth interval for the next child
        self._birth_interval = calc_birth_interval()
        for parent in [self, father]:
            parent._children.append(baby)
        return baby

    def is_married(self):
        "Returns a boolean indicating if person is married or not."
        if self._spouse == None:
            return False
        else:
            return True

    def __str__(self):
        return "Person(PID: %s. Household: %s. Neighborhood: %s)" %(self.get_ID(), self.get_parent_agent().get_ID(), self.get_parent_agent().get_parent_agent().get_ID())

class Household(Agent_set):
    "Represents a single household agent"
    def __init__(self, world, ID=None, initial_agent=False):
        Agent_set.__init__(self, world, ID, initial_agent)
        self._any_non_wood_fuel = boolean_choice(.93) # From DS0002$BAE15
        self._own_house_plot = boolean_choice(.829)  # From DS0002$BAA43
        self._own_land = boolean_choice(.61) # From Axinn, Ghimire (2007)
        self._rented_out_land = boolean_choice(.11) # From Axinn, Ghimire (2007)
        self._lastmigrant_time = None
        self._hh_area = 0 # Area of house plot in square meters

    def any_non_wood_fuel(self):
        "Boolean for whether household uses any non-wood fuel"
        return self._any_non_wood_fuel
    
    def get_hh_head(self):
        max_age = None
        if self.num_members() == 0:
            raise AgentError("No household head for household %s. Household has no members"%self.get_ID())
        for person in self.get_agents():
            if person.get_age() > max_age:
                max_age = person.get_age()
                hh_head = person
        return hh_head

    def own_house_plot(self):
        "Boolean for whether household owns the plot of land on which it resides"
        return self._own_house_plot

    def own_any_land(self):
        "Boolean for whether household owns any land"
        return self._own_land

    def rented_out_land(self):
        "Boolean for whether household rented out any of its land"
        return self._rented_out_land

    def is_initial_agent(self):
        return self._initial_agent

    def fw_usage(self, time):
        fw_usage = calc_fuelwood_usage(self, time)
        # Convert daily fw_usage to monthly
        fw_usage = fw_usage * 30
        return fw_usage

    def remove_agent(self, person):
        """
        Remove a person from this household. Override the default method for an 
        Agent_set so that we can check if the removal of this agent would leave 
        this household empty. It it would leave it empty, they destroy this 
        household after removing the agent. Otherwise, run the normal method 
        for agent removal from a household Agent_set.
        """
        Agent_set.remove_agent(self, person)
        #if self.num_members() == 0:
        #    print "%s left empty - household removed from model"%self
        #    neighborhood = self.get_parent_agent()
        #    neighborhood._land_agveg += self._hh_area
        #    neighborhood._land_privbldg -= self._hh_area
        #    neighborhood.remove_agent(neighborhood)

    def __str__(self):
        return "Household(HID: %s. %s person(s))"%(self.get_ID(), self.num_members())

class Neighborhood(Agent_set):
    "Represents a single neighborhood agent"
    def __init__(self, world, ID=None, initial_agent=False):
        Agent_set.__init__(self, world, ID, initial_agent)
        self._avg_years_nonfamily_services = None
        self._elec_available = None
        self._land_agveg = None
        self._land_nonagveg = None
        self._land_privbldg = None
        self._land_pubbldg = None
        self._land_other = None
        self._distnara = None
        self._x = None # x coordinate in UTM45N
        self._y = None # y coordinate in UTM45N
        self._elev = None # Elevation of neighborhood from SRTM DEM

    def add_agent(self, agent, initializing=False):
        """
        Subclass the Agent_set.add_agent function in order to account for LULC 
        change with new household addition.
        """
        # The "initializing" variable allows ignoring the land cover 
        # addition/subtraction while initializing the model with the CVFS data.
        if initializing==True:
            Agent_set.add_agent(self, agent)
        else:
            hh_area = calc_hh_area()
            if self._land_agveg - hh_area < 0:
                if self._land_nonagveg - hh_area < 0:
                    return False
                else:
                    self._land_nonagveg -= hh_area
                    self._land_privbldg += hh_area
                    Agent_set.add_agent(self, agent)
                    return True
            else:
                self._land_agveg -= hh_area
                self._land_privbldg += hh_area
                Agent_set.add_agent(self, agent)
                return True
            # Should never get to this line:
            return False

    def is_initial_agent(self):
        return self._initial_agent

    def avg_years_nonfamily_services(self):
        "Average number of years non-family services have been available."
        return self._avg_years_nonfamily_services

    def elec_available(self):
        "Boolean for whether neighborhood has electricity."
        return self._elec_available

    def get_num_psn(self):
        "Returns the number of people in the neighborhood."
        num_psn = 0
        for household in self.iter_agents():
            num_psn += household.num_members()
        return num_psn

    def get_num_marriages(self):
        "Returns the total number of marriages in this neighborhood."
        num_marr = 0
        spouses = []
        for household in self.iter_agents():
            for person in household.iter_agents():
                if person.is_married() and (person.get_spouse() not in spouses):
                    num_marr += 1
                    spouses.append(person)
        return num_marr

    def get_hh_sizes(self):
        hh_sizes = {}
        for household in self.iter_agents():
            hh_sizes[household.get_ID()] = household.num_members()
        return hh_sizes

    def get_coords(self):
        return self._x, self._y

    def __str__(self):
        return "Neighborhood(NID: %s. %s household(s))" %(self.get_ID(), self.num_members())

class Region(Agent_set):
    """Represents a set of neighborhoods sharing a spatial area (and therefore 
    land use data), and demographic characteristics."""
    def __init__(self, world, ID=None, initial_agent=False):
        Agent_set.__init__(self, world, ID, initial_agent)

        # The agent_store instance is used to store migrants while they are 
        # away from their household (prior to their return).
        self.agent_store = Agent_Store()

        # TODO: Here demographic variables could be setup specific for each 
        # region - these could be used to represent different strata.

    def __repr__(self):
        #TODO: Finish this
        return "__repr__ UNDEFINED"

    def __str__(self):
        return "Region(RID: %s, %s neighborhood(s), %s household(s), %s person(s))"%(self.get_ID(), \
                len(self._members), self.num_households(), self.num_persons())

    def is_initial_agent(self):
        return self._initial_agent

    def iter_households(self):
        "Returns an iterator over all the households in the region"
        for neighborhood in self.iter_agents():
            for household in neighborhood.iter_agents():
                yield household

    def iter_persons(self):
        "Returns an iterator over all the persons in the region"
        for household in self.iter_households():
            for person in household.iter_agents():
                yield person

    def births(self, time):
        """Runs through the population and agents give birth probabilistically 
        based on their birth interval and desired family size."""
        births = {}
        for household in self.iter_households():
            for person in household.iter_agents():
                if person.is_eligible_for_birth(time):
                    # Agent gives birth. First find the father (assumed to be 
                    # the spouse of the person giving birth).
                    father = person.get_spouse()
                    # Now have the mother give birth, and add the 
                    # new person to the mother's household.
                    household.add_agent(person.give_birth(time,
                        father=father))
                    if rcParams['feedback.birth.nonagveg']:
                        neighborhood = household.get_parent_agent()
                        if (neighborhood._land_nonagveg - rcParams['feedback.birth.nonagveg.area']) >= 0:
                            neighborhood._land_nonagveg -= rcParams['feedback.birth.nonagveg.area']
                            neighborhood._land_other += rcParams['feedback.birth.nonagveg.area']
                    # Track the total number of births for each 
                    # timestep by neighborhood.
                    if not births.has_key(neighborhood.get_ID()):
                        births[neighborhood.get_ID()] = 0
                    births[neighborhood.get_ID()] += 1
        return births
                        
    def deaths(self, time):
        """Runs through the population and kills agents probabilistically based 
        on their age and sex and the probability.death for this population"""
        deaths = {}
        for household in self.iter_households():
            for person in household.iter_agents():
                if random_state.rand() < calc_probability_death(person):
                    # Agent dies.
                    person.kill(time)
                    neighborhood = household.get_parent_agent()
                    if not deaths.has_key(neighborhood.get_ID()):
                        deaths[neighborhood.get_ID()] = 0
                    deaths[neighborhood.get_ID()] += 1
        return deaths
                        
    def marriages(self, time):
        """Runs through the population and marries agents probabilistically 
        based on their age and the probability_marriage for this population"""
        # First find the eligible agents
        minimum_age = rcParams['marriage.minimum_age_years']
        maximum_age = rcParams['marriage.maximum_age_years']
        eligible_males = []
        eligible_females = []
        for household in self.iter_households():
            for person in household.iter_agents():
                if (not person.is_married()) and \
                        (person.get_age()/12 >= minimum_age) and \
                        (person.get_age()/12 <= maximum_age) and \
                        (random_state.rand() < calc_probability_marriage(person)):
                    # Agent is eligible to marry.
                    if person.get_sex() == "male":
                        eligible_males.append(person)
                    else:
                        eligible_females.append(person)
        # As a crude model of in-migration, append to the list additional 
        # agents, according to a parameter specifying the proportion of persons 
        # who marry in-migrants.
        num_new_females = int(np.floor(rcParams['prob.marry.inmigrant'] * len(eligible_females)))
        for n in xrange(1, num_new_females):
            # Choose the age randomly from the ages of the eligible females
            agent_age = eligible_females[np.random.randint(len(eligible_females))].get_age()
            agent_ethnicity = eligible_females[np.random.randint(len(eligible_females))].get_ethnicity()
            eligible_females.append(self._world.new_person(time, sex="female", age=agent_age, ethnicity=agent_ethnicity))

        num_new_males = int(np.floor(rcParams['prob.marry.inmigrant'] * len(eligible_males)))
        for n in xrange(1, num_new_males):
            # Choose the age randomly from the ages of the eligible males
            agent_age = eligible_males[np.random.randint(len(eligible_males))].get_age()
            agent_ethnicity = eligible_males[np.random.randint(len(eligible_males))].get_ethnicity()
            eligible_males.append(self._world.new_person(time, sex="male", age=agent_age, ethnicity=agent_ethnicity))

        # Now pair up the eligible agents. Any extra males/females will not 
        # marry this timestep.
        couples = []
        for male in eligible_males:
            # The 'choose_spouse' function in statistics.py chooses a spouse 
            # based on the probability of the man marrying each woman in the 
            # eligible_females list (with the probability dependent on the age 
            # difference between the man and each woman in the list.
            if len(eligible_females) == 0: break
            female = choose_spouse(male, eligible_females)
            eligible_females.remove(female)
            couples.append((male, female))

        marriages = {}
        # Now marry the agents
        for male, female in couples:
            # First marry the agents.
            male.marry(female, time)
            female._first_birth_timing = calc_first_birth_time(self)
            moveout_prob = rcParams['prob.marriage.moveout']
            # Create a new household according to the moveout probability
            if boolean_choice(moveout_prob) or male.get_parent_agent()==None:
                # Create a new household. male.get_parent_agent() is equal to 
                # None for in-migrants, as they are not a member of a 
                # household.
                new_home = self._world.new_household()
                neighborhoods = [] # Possible neighborhoods for the new_home
                for person in [male, female]:
                    old_household = person.get_parent_agent() # this person's old household
                    if old_household == None:
                        # old_household will equal none for in-migrants, as 
                        # they are not tracked in the model until after this 
                        # timestep. This means they also will not have a 
                        # neighborhood.
                        continue
                    old_household.remove_agent(person)
                    new_home.add_agent(person)
                    neighborhoods.append(old_household.get_parent_agent()) # this persons old neighborhood
                # Assign the new household to the male or females neighborhood. 
                # Or randomly pick new neighborhood if both members of the 
                # couple are in-migrants.
                if len(neighborhoods)>0:
                    # len(neighborhoods) is greater than zero if at least one 
                    # is NOT an in-migrant. Choose male's neighborhood by 
                    # default.
                    neighborhood = neighborhoods[0]
                else:
                    poss_neighborhoods = self.get_agents()
                    neighborhood = poss_neighborhoods[np.random.randint( \
                        len(poss_neighborhoods))]
                # Try to add the household to the chosen neighborhood. If
                # the add_agent function returns false it means there is no 
                # available land in the chosen neighborhood, so pick another 
                # neighborhood, iterating through the closest neighborhoods 
                # until one is found with adequate land:
                n = 0
                while neighborhood.add_agent(new_home) == False:
                    neighborhood = neighborhood._neighborhoods_by_distance[n]
                    n += 1
            else:
                # Otherwise they stay in the male's household. So have the 
                # female move in.
                old_household = female.get_parent_agent() # this person's old household
                # old_household will equal none for in-migrants, as they are 
                # not tracked in the model until after this timestep.
                if old_household != None: old_household.remove_agent(female)
                male_household = male.get_parent_agent()
                male_household.add_agent(female)
                neighborhood = male.get_parent_agent().get_parent_agent()
            if not marriages.has_key(neighborhood.get_ID()):
                marriages[neighborhood.get_ID()] = 0
            marriages[neighborhood.get_ID()] += 1
        return marriages

    def get_num_marriages(self):
        "Returns the total number of marriages in this region."
        num_marr = 0
        spouses = []
        for person in self.iter_persons():
            if person.is_married() and (person.get_spouse() not in spouses):
                    num_marr += 1
                    spouses.append(person)
        return num_marr

    def education(self, time):
        """
        Runs through the population and makes agents probabilistically attend 
        schooling based on their age and the education function for this 
        population.
        """
        timestep = rcParams['model.timestep']
        start_school_age = rcParams['education.start_school_age_years']
        schooling = {}
        for person in self.iter_persons():
            if person._school_status == "outofschool":
                pass
            elif (person._school_status == "undetermined") & (person.get_age()/12 >= start_school_age):
                person._school_status = "inschool"
                person._final_schooling_level = calc_education_level(person)
                person._schooling = timestep / 12
            elif person._school_status == "inschool":
                if person._schooling >= person._final_schooling_level:
                    person._school_status = "outofschool"
                else:
                    person._schooling += timestep / 12
            neighborhood = person.get_parent_agent().get_parent_agent()
            #if not schooling.has_key(neighborhood.get_ID()):
            #    schooling[neighborhood.get_ID()] = person._schooling
            #schooling[neighborhood.get_ID()] += 1
        return schooling

    def migrations(self, time):
        """
        Runs through the population and makes agents probabilistically migrate
        based on their age and the probability_marriage for this population.
        """
        # First handle out-migrations
        out_migr = {}
        for household in self.iter_households():
            for person in household.iter_agents():
                if random_state.rand() < calc_probability_migration(person):
                    household._lastmigrant_time = time
                    # Agent migrates. Choose how long the agent is migrating 
                    # for from a probability distribution.
                    months_away = calc_migration_length(person)
                    # The add_agent function of the agent_store class also 
                    # handles removing the agent from its parent (the 
                    # household).
                    self.agent_store.add_agent(person, time+(months_away/12))
                    neighborhood = household.get_parent_agent()
                    if not out_migr.has_key(neighborhood.get_ID()):
                        out_migr[neighborhood.get_ID()] = 0
                    out_migr[neighborhood.get_ID()] += 1

        # Now handle the returning migrants (based on the return times assigned 
        # to them when they initially outmigrated)
        return_migr = self.agent_store.release_agents(time)
        new_in_migr = {}
        return out_migr, return_migr, new_in_migr

    def increment_age(self):
        """Adds one to the age of each agent. The units of age are dependent on 
        the units of the input rc parameters."""
        for person in self.iter_persons():
            timestep = rcParams['model.timestep']
            person._age += timestep

    def get_neighborhood_fw_usage(self, time):
        fw_usage = {}
        for neighborhood in self.iter_agents():
            fw_usage[neighborhood.get_ID()] = 0
            for household in neighborhood.iter_agents():
                fw_usage[neighborhood.get_ID()] += household.fw_usage(time)
        return {'fw_usage': fw_usage}

    def get_neighborhood_landuse(self):
        landuse = {'agveg':{}, 'nonagveg':{}, 'privbldg':{}, 'pubbldg':{}, 'other':{}}
        for neighborhood in self.iter_agents():
            landuse['agveg'][neighborhood.get_ID()] = neighborhood._land_agveg
            landuse['nonagveg'][neighborhood.get_ID()] = neighborhood._land_nonagveg
            landuse['privbldg'][neighborhood.get_ID()] = neighborhood._land_privbldg
            landuse['pubbldg'][neighborhood.get_ID()] = neighborhood._land_pubbldg
            landuse['other'][neighborhood.get_ID()] = neighborhood._land_other
        return landuse

    def get_neighborhood_pop_stats(self):
        """
        Used each timestep to return a dictionary of neighborhood-level 
        population statistics.
        """
        pop_stats = {'num_psn':{}, 'num_hs':{}, 'num_marr':{}}
        for neighborhood in self.iter_agents():
            if not pop_stats.has_key(neighborhood.get_ID()):
                pop_stats[neighborhood.get_ID()] = {}
            pop_stats['num_psn'][neighborhood.get_ID()] = neighborhood.get_num_psn()
            pop_stats['num_hs'][neighborhood.get_ID()] = neighborhood.num_members()
            pop_stats['num_marr'][neighborhood.get_ID()] = neighborhood.get_num_marriages()
        return pop_stats

    def num_persons(self):
        "Returns the number of persons in the population."
        total = 0
        for household in self.iter_households():
            total += household.num_members()
        return total

    def num_households(self):
        total = 0
        for neighborhood in self.iter_agents():
            total += len(neighborhood.get_agents())
        return total

    def num_neighborhoods(self):
        return len(self._members.values())

class World():
    """The world class generates new agents, while tracking ID numbers to 
    ensure that they are always unique across each agent type. It also contains 
    a dictionary with all the regions in the model."""
    def __init__(self):
        # _members stores member regions in a dictionary keyed by RID
        self._members = {}

        # These IDGenerator instances generate unique ID numbers that are never 
        # reused, and always unique (once used an ID number cannot be 
        # reassigned to another agent). All instances of the Person class, for  
        # example, will have a unique ID number generated by the PIDGen 
        # IDGenerator instance.
        self._PIDGen = IDGenerator()
        self._HIDGen = IDGenerator()
        self._NIDGen = IDGenerator()
        self._RIDGen = IDGenerator()

    def set_DEM_data(self, DEM, gt, prj):
        self._DEM_array = DEM
        self._DEM_gt = gt
        self._DEM_prj = prj
        return 0

    def get_DEM(self):
        return self._DEM_array

    def get_DEM_data(self):
        return self._DEM_array, self._DEM_gt, self._DEM_prj

    def set_world_mask_data(self, world_mask, gt, prj):
        self._world_mask_array = world_mask
        self._world_mask_gt = gt
        self._world_mask_prj = prj
        return 0

    def get_world_mask(self):
        return self._world_mask_array

    def get_world_mask_data(self):
        return self._world_mask_array, self._world_mask_gt, self._world_mask_prj

    def new_person(self, birthdate, PID=None, mother=None, father=None, age=0,
            sex=None, initial_agent=False, ethnicity=None):
        "Returns a new person agent."
        if PID == None:
            PID = self._PIDGen.next()
        else:
            # Update the generator so the PID will not be reused
            self._PIDGen.use_ID(PID)
        return Person(self, birthdate, PID, mother, father, age, sex, initial_agent, ethnicity)

    def new_household(self, HID=None, initial_agent=False):
        "Returns a new household agent."
        if HID == None:
            HID = self._HIDGen.next()
        else:
            # Update the generator so the HID will not be reused
            self._HIDGen.use_ID(HID)
        return Household(self, HID, initial_agent)

    def new_neighborhood(self, NID=None, initial_agent=False):
        "Returns a new neighborhood agent."
        if NID == None:
            NID = self._NIDGen.next()
        else:
            # Update the generator so the NID will not be reused
            self._NIDGen.use_ID(NID)
        return Neighborhood(self, NID, initial_agent)

    def new_region(self, RID=None, initial_agent=False):
        "Returns a new region agent, and adds it to the world member list."
        if RID == None:
            RID = self._RIDGen.next()
        else:
            # Update the generator so the RID will not be reused
            self._RIDGen.use_ID(RID)
        region = Region(self, RID, initial_agent)
        self._members[region.get_ID()] = region
        return region

    def get_regions(self):
        return self._members.values()

    def iter_regions(self):
        "Convenience function for iteration over all regions in the world."
        for region in self._members.values():
            yield region

    def iter_persons(self):
        "Convenience function used for things like incrementing agent ages."
        for region in self.iter_regions():
            for person in region.iter_persons():
                yield person

    def write_persons_to_csv(self, timestep, results_path):
        """
        Writes a list of persons, with a header row, to CSV.
        """
        psn_csv_file = os.path.join(results_path, "psns_time_%s.csv"%timestep)
        out_file = open(psn_csv_file, "w")
        csv_writer = csv.writer(out_file)
        csv_writer.writerow(["pid", "hid", "nid", "rid", "gender", "ethnicity", "age", "spouseid", "father_id", "mother_id", "des_num_children", "first_birth_timing"])
        for region in self.iter_regions():
            for person in region.iter_persons():
                new_row = []
                new_row.append(person.get_ID())
                new_row.append(person.get_parent_agent().get_ID())
                new_row.append(person.get_parent_agent().get_parent_agent().get_ID())
                new_row.append(person.get_parent_agent().get_parent_agent().get_parent_agent().get_ID())
                new_row.append(person.get_sex())
                new_row.append(person.get_ethnicity())
                new_row.append(person.get_age())
                spouse = person.get_spouse()
                if spouse != None:
                    new_row.append(person.get_spouse().get_ID())
                else:
                    new_row.append(None)
                if person._mother != None:
                    new_row.append(person._mother.get_ID())
                else: 
                    new_row.append(None)
                if person._father != None:
                    new_row.append(person._father.get_ID())
                else: 
                    new_row.append(None)
                new_row.append(person._des_num_children)
                new_row.append(person._first_birth_timing)
                csv_writer.writerow(new_row)
        out_file.close()

    def write_NBHs_to_csv(self, timestep, results_path):
        """
        Writes a list of neighborhoods, with a header row, to CSV.
        """
        NBH_csv_file = os.path.join(results_path, "NBHs_time_%s.csv"%timestep)
        out_file = open(NBH_csv_file, "w")
        csv_writer = csv.writer(out_file)
        csv_writer.writerow(["nid", "rid", "x", "y", "numpsns", "numhs", "agveg",
            "nonagveg", "pubbldg", "privbldg", "other", "total_area",
            "perc_agveg", "perc_veg", "perc_bldg"])
        for region in self.iter_regions():
            for neighborhood in region.iter_agents():
                new_row = []
                new_row.append(neighborhood.get_ID())
                new_row.append(neighborhood.get_parent_agent().get_ID())

                x, y = neighborhood.get_coords()
                new_row.append(x)
                new_row.append(y)

                new_row.append(neighborhood.get_num_psn())
                new_row.append(neighborhood.num_members())

                new_row.append(neighborhood._land_agveg)
                new_row.append(neighborhood._land_nonagveg)
                new_row.append(neighborhood._land_pubbldg)
                new_row.append(neighborhood._land_privbldg)
                new_row.append(neighborhood._land_other)

                total_area = neighborhood._land_agveg + neighborhood._land_nonagveg + \
                        neighborhood._land_pubbldg + neighborhood._land_privbldg + \
                        neighborhood._land_other
                perc_agveg = neighborhood._land_agveg / total_area
                perc_veg = (neighborhood._land_agveg + neighborhood._land_nonagveg) \
                        / total_area
                perc_bldg = (neighborhood._land_privbldg + neighborhood._land_pubbldg) \
                        / total_area

                new_row.append(total_area)
                new_row.append(perc_agveg)
                new_row.append(perc_veg)
                new_row.append(perc_bldg)

                csv_writer.writerow(new_row)
        out_file.close()
