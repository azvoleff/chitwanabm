"""
Part of Chitwan Valley agent-based model.

Sets up a chitwanABM model run: Initializes neighborhood/household/person agents 
and land use using the original CVFS data.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import pickle

from chitwanABM import rcParams
from chitwanABM.agents import World

def read_CVFS_data(textfile, key_field):
    """Reads in CVFS data from a CSV file into a dictionary of dictionary 
    objects, where the first line of the file gives the column headings (used 
    as keys within the nested dictionary object). No conversion of the fields 
    is done: they are all stored as strings, EXCEPT for the key_field, which is 
    converted and stored as an int."""

    try:
        file = open(textfile, 'r')
        lines = file.readlines()
        file.close()
    except:
        raise IOError("error reading %s"%(textfile))
    
    # The first line of the data file gives the column names
    col_names = lines[0].split(',')
    for n in xrange(len(col_names)):
        col_names[n] = col_names[n].strip('\n \"')

    data = {}
    for line in lines[1:]:
        fields = line.split(',')
        for n in xrange(len(fields)):
            fields[n] = fields[n].strip('\n \"')

        new_data = {} 
        for field, column_name in zip(fields, col_names):
            new_data[column_name] = field

        data_key = int(new_data[key_field])
        if new_data.has_key(data_key):
            raise KeyError('key %s is already in use'%(data_key))
        data[data_key] = new_data

    return data

def assemble_neighborhoods(neighborhoodsFile, model_world):
    """Reads in data from the CVFS (from dataset DS0014) on number of years 
    non-family services were available within a 30 min walk of each 
    neighborhood (SCHLFT, HLTHFT, BUSFT, MARFT, EMPFT) and on whether 
    neighborhood was electrified (ELEC)."""
    neigh_datas = read_CVFS_data(neighborhoodsFile, "NEIGHID") 

    neighborhoods = []
    for neigh_data in neigh_datas.itervalues():
        NEIGHID = int(neigh_data["NEIGHID"])
        neighborhood = model_world.new_neighborhood(NEIGHID, initial_agent=True)
        neighborhood._avg_years_nonfamily_services = float(neigh_data["AVG_YRS_SRVC"])
        neighborhood._elec_available =  bool(neigh_data['ELEC_AVAIL']) # is neighborhood electrified (in 1995/1996)
        neighborhoods.append(neighborhood)

    return neighborhoods

def assemble_households(householdsFile, model_world):
    """Reads in data from the CVFS (from dataset DS0002) on several statistics 
    for each household (BAA43, BAA44, BAA10A, BAA18A)."""
    household_datas = read_CVFS_data(householdsFile, "HHID")
    
    households = []
    HHID_NEIGHID_map = {} # Links persons with their HHID
    for household_data in household_datas.itervalues():
        HHID = int(household_data['HHID'])
        NEIGHID = int(household_data['NEIGHID'])
        HHID_NEIGHID_map[HHID] = NEIGHID
        
        household = model_world.new_household(HHID, initial_agent=True)
        household._own_house_plot = bool(household_data['BAA43']) # does the household own the plot of land the house is on
        household._rented_out_land = int(household_data['BAA44']) # does the household rent out any land

        own_any_bari = bool(household_data['BAA10A']) # does the household own any bari land
        own_any_khet = bool(household_data['BAA18A']) # does the household own any khet land

        if own_any_bari or own_any_khet or household._own_household_plot:
            household._own_any_land = True
        else:
            household._own_any_land = False

        households.append(household)

    return households, HHID_NEIGHID_map

def assemble_persons(relationshipsFile, model_world):
    """Reads data in from the CVFS census (dataset DS0004 (restricted)) and 
    from the household relationship grid, CVFS DS0016 (restricted), which were 
    combined into one file, hhrel.csv, by the data_preprocess.R R script. This 
    function then assembles person agents from the data, including their 
    relationships (parent, child, etc.) with other agents.."""
    relations = read_CVFS_data(relationshipsFile, "RESPID") 

    # For each household, create a SUBJECT -> RESPID mapping.  For example:
    # SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID
    SUBJECT_RESPID_map = {}
    for relation in relations.itervalues():
        RESPID = int(relation['RESPID'])
        SUBJECT = int(relation['SUBJECT'])
        HHID = int(relation['HHID'])
        if SUBJECT_RESPID_map.has_key(HHID):
            SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID
        else:
            SUBJECT_RESPID_map[HHID] = {}
            SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID

    # Loop over all agents in the relationship grid.
    personsDict = {}
    RESPID_HHID_map = {} # Links persons with their HHID
    for relation in relations.itervalues():
        RESPID = int(relation['RESPID'])
        HHID = int(relation['HHID'])
        RESPID_HHID_map[RESPID] = HHID

        # Get the agent's sex and age
        try:
            AGEMNTHS = int(relation['AGEMNTHS']) # Age of agent in months
            CENGENDR = relation['CENGENDR']
        except KeyError:
            print "WARNING: no census data on person %s. This agent will be excluded from the model."%(RESPID)
            continue
        except ValueError:
            print "WARNING: no census data on person %s. This agent will be excluded from the model."%(RESPID)
            continue
        
        # Read in SUBJECT IDs of parents/spouse/children
        mother_SUBJECT = int(relation['PARENT1'])
        father_SUBJECT = int(relation['PARENT2'])
        spouse_SUBJECT = int(relation['SPOUSE1'])

        # Convert SUBJECT IDs into RESPIDs
        if father_SUBJECT != 0:
            try:
                father_RESPID = SUBJECT_RESPID_map[HHID][father_SUBJECT]
            except KeyError:
                print "WARNING: father of person %s was excluded from the model. Person %s will have their father field set to None."%(RESPID, RESPID)
            father_RESPID = None
        else:
            father_RESPID = None

        if mother_SUBJECT != 0:
            try:
                mother_RESPID = SUBJECT_RESPID_map[HHID][mother_SUBJECT]
            except KeyError:
                print "WARNING: mother of person %s was excluded from the model. Person %s will have their mother field set to None."%(RESPID, RESPID)
            mother_RESPID = None
        else:
            mother_RESPID = None

        if spouse_SUBJECT != 0:
            try:
                spouse_RESPID = SUBJECT_RESPID_map[HHID][spouse_SUBJECT]
            except KeyError:
                print "WARNING: spouse of person %s was excluded from the model. Person %s will have their spouse field set to None."%(RESPID, RESPID)
                spouse_RESPID = None
        else:
            spouse_RESPID = None

        # Convert numerical genders to "male" or "female". 1 = male, 2 = female
        if CENGENDR == '1':
            CENGENDR = "male"
        elif CENGENDR == '2':
            CENGENDR = "female"

        # Finally, make the new person.
        person = model_world.new_person(None, RESPID, mother_RESPID, father_RESPID, AGEMNTHS, 
                CENGENDR, initial_agent=True)
        person._spouse = spouse_RESPID

        personsDict[RESPID] = person

    # Now, for each person in the personsDict, convert the RESPIDs for mother, 
    # father, and spouse to be references to the actual instances  of the 
    # mother, father and spouse agents.
    persons = []
    for person in personsDict.values():
        try:
            if person._mother != None:
                person._mother = personsDict[person._mother]
                if person._mother == person:
                    print "WARNING: agent %s skipped because it is it's own mother"%(person.get_ID())
                    continue
            if person._father != None:
                person._father = personsDict[person._father]
                if person._father == person:
                    print "WARNING: agent %s skipped because it is it's own father"%(person.get_ID())
                    continue
            if person._spouse != None:
                person._spouse = personsDict[person._spouse]
                if person._spouse == person:
                    print "WARNING: agent %s skipped because it is married to itself"%(person.get_ID())
                    continue
            persons.append(person)
        except KeyError:
            print "WARNING: person %s skipped due to mother/father/spouse KeyError. This agent will be excluded from the model."%(person.get_ID())
            
    return persons, RESPID_HHID_map

def assemble_world():
    """Puts together a single region from the CVFS data using the above 
    functions to input restricted CVFS data on persons, households, and 
    neighborhoods."""
    model_world = World()

    relationships_grid_file = rcParams['input.relationships_grid_file']
    households_file = rcParams['input.households_file']
    neighborhoods_file = rcParams['input.neighborhoods_file']

    persons, RESPID_HHID_map = assemble_persons(relationships_grid_file, model_world)
    households, HHID_NEIGHID_map = assemble_households(households_file, model_world)
    neighborhoods = assemble_neighborhoods(neighborhoods_file, model_world)

    # Populate the Chitwan region (the code could handle multiple regions too, 
    # for instance, subdivide the population into different groups with 
    # different hazards of migration. Currently just one region is used.
    region = model_world.new_region()

    for neighborhood in neighborhoods:
        region.add_agent(neighborhood)

    # Now populate the neighborhoods with households. For this we need the HHID 
    # -> NID mapping:
    for household in households:
        HHID = household.get_ID()
        NEIGHID = HHID_NEIGHID_map[HHID]
        # Get a reference to this neighborhood, and add the household
        neighborhood = region.get_agent(NEIGHID)
        neighborhood.add_agent(household)

    # Now populate the households with people. For this we need the RESPID -> 
    # HHID mapping and the HHID -> NEIGHID map.
    for person in persons:
        RESPID = person.get_ID()
        HHID = RESPID_HHID_map[RESPID]
        try:
            NEIGHID = HHID_NEIGHID_map[HHID]
        except KeyError:
            print "WARNING: household %s is not in DS0002. This agent will be excluded from the model."%(HHID)
            continue
        # Get a reference to this neighborhood
        neighborhood = region.get_agent(NEIGHID)
        # Then get a reference to the proper household, and add the person
        household = neighborhood.get_agent(HHID)
        household.add_agent(person)

    print "\nPersons: %s, Households: %s, Neighborhoods: %s"%(region.num_persons(), region.num_households(), region.num_neighborhoods())
    return model_world

def save_world(world, filename):
    "Pickles a world for later reloading."
    file = open(filename, "w")
    pickle.dump(world, file)
