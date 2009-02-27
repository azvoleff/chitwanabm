""":
Part of Chitwan Valley agent-based model.

Sets up a CV_ABM_NS model run: Initializes neighborhood/household/person agents 
and land use based on a set of distributions for the value of particular 
characteristics for each agent.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

from chitwanABM import rcParams
from chitwanABM.agents import Person, Household, Neighborhood

def read_CVFS_data(textfile):
    """Reads in CVFS data from a CSV file into a list of dictionary objects, 
    where the first line of the file gives the column headings (used as keys 
    within the nested dictionary object). No conversion of the fields is done: 
    they are all stored as strings."""

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

    data = []

    for line in lines[1:]:
        fields = line.split(',')
        for n in xrange(len(fields)):
            fields[n] = fields[n].strip('\n \"')

        new_data = {} 
        for field, column_name in zip(fields, col_names):
            new_data[column_name] = field

        data.append(new_data)

    return data

def assemble_neighborhoods(neighborhoodsFile):
    """Reads in data from the CVFS (from dataset DS0014) on number of years 
    non-family services were available within a 30 min walk of each 
    neighborhood (SCHLFT, HLTHFT, BUSFT, MARFT, EMPFT) and on whether 
    neighborhood was electrified (ELEC)."""
    neigh_datas = read_CVFS_data(neighborhoodsFile) 

    neighborhoods = []
    for neigh_data in neigh_datas:
        NEIGHID = int(neigh_data["NEIGHID"])
        neighborhood = Neighborhood(NEIGHID, initial_agent=True)

        # Axinn (2007) uses the "average number of years non-family services 
        # were within a 30 minute walk" so, compute this:
        yrs_nonfamily_services = 0
        yrs_nonfamily_services += int(neigh_data['SCHLFT']) # years schools w/in 30 min walk
        yrs_nonfamily_services += int(neigh_data['HLTHFT']) # years health w/in 30 min walk
        yrs_nonfamily_services += int(neigh_data['BUSFT']) # years bus w/in 30 min walk
        yrs_nonfamily_services += int(neigh_data['MARFT']) # years market w/in 30 min walk
        yrs_nonfamily_services += int(neigh_data['EMPFT']) # years employer w/in 30 min walk
        neighborhood.__avg_years_nonfamily_services = yrs_nonfamily_services / 5

        neighborhood._elec_available =  bool(neigh_data['ELEC']) # is neighborhood electrified

        neighborhoods(neighborhood)

        return neighborhoods

def assemble_households(householdsFile):
    """Reads in data from the CVFS (from dataset DS0002) on several statistics 
    for each household (BAA43, BAA44, BAA10A, BAA18A)."""
    household_datas = read_CVFS_data(householdsFile) 
    
    households = []
    HHID_NEIGHID_map = {} # Links persons with their HHID
    for household_data in household_datas:
        HHID = int(household_data['HHID'])
        NEIGHID = int(household_data['NEIGHID'])
        HHID_NEIGHID_map[HHID] = NEIGHID
        
        household = Household(HHID, initial_agent=True)
        household._own_house_plot = bool(household_data['BAA43']) # does the household own the plot of land the house is on
        household._rented_out_land = int(household_data['BAA44']) # does the household rent out any land

        # NOTE: Need to handle households where this question was 
        # innappropriate (where they did no farming)
        own_any_bari = bool(household_data['BAA10A']) # does the household own any bari land
        own_any_khet = bool(household_data['BAA18A']) # does the household own any khet land

        if own_any_bari or own_any_khet or household._own_household_plot:
            household._own_any_land = True
        else:
            household._own_any_land = False

        households.append(household)

    return households, HHID_NEIGHID_map

def assemble_persons(relationshipsFile, censusFile):
    """Reads data in from the CVFS census (dataset DS0003 (public) or 
    DS0004 (restricted)) and from the household relationship grid, CVFS 
    dataset DS0015 (public) or DS0016 (restricted), and assembles person, 
    household, neighborhood, and region agents."""
    relations = read_CVFS_data(relationshipsFile) 
    census = read_CVFS_data(censusFile) 

    # For each household, create a SUBJECT -> RESPID mapping.  For example:
    # SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID
    SUBJECT_RESPID_map = {}
    for relation in relations:
        RESPID = int(relation['RESPID'])
        SUBJECT = int(relation['SUBJECT'])
        HHID = int(relation['HHID'])
        if SUBJECT_RESPID_map.has_key(HHID):
            SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID
        else:
            SUBJECT_RESPID_map[HHID] = {}
            SUBJECT_RESPID_map[HHID][SUBJECT] = RESPID

    # Loop over all agents in the relationship grid.
    persons = []
    RESPID_HHID_map = {} # Links persons with their HHID
    for relation in persons:
        RESPID = int(relation['RESPID'])
        HHID = int(relation['HHID'])
        RESPID_HHID_map[RESPID] = HHID

        # Get the agent's sex and age from the census data
        CENAGE = int(census[RESPID]['CENAGE'])
        CENGENDR = census[RESPID]['CENGENDR']
        
        # Read in SUBJECT RESPIDs of parents/spouse/children
        mother_SUBJECT = int(relations[RESPID]['PARENT1'])
        father_SUBJECT = int(relations[RESPID]['PARENT2'])
        spouse_SUBJECT = int(relations[RESPID]['SPOUSE1'])


        # Convert SUBJECT IDs into RESPIDs
        father_RESPID = SUBJECT_RESPID_map[HHID][father_SUBJECT]
        mother_RESPID = SUBJECT_RESPID_map[HHID][mother_SUBJECT]
        spouse_RESPID = SUBJECT_RESPID_map[HHID][spouse_SUBJECT]

        person = Person(None, RESPID, mother_RESPID, father_RESPID, CENAGE, CENGENDR, initial_agent=True)

        persons.append(person)

    return persons, RESPID_HHID_map

def assemble_region(region):
    """Puts together a region from the CVFS data using the above functions to 
    input restricted CVFS data on persons, households, and neighborhoods."""
    census_file = rcParams['input.census_file']
    relationships_grid_file = rcParams['input.relationships_grid_file']
    households_file = rcParams['input.households_file']
    neighborhoods_file = rcParams['input.neighborhoods_file']

    persons, RESPID_HHID_map = assemble_persons(relationships_grid_file, census_file)
    households, HHID_NEIGHID_map = assemble_households(households_file)
    neighborhoods = assemble_neighborhoods(neighborhoods_file)

    # Populate the region
    for neighborhood in neighborhoods:
        Region.add_agent(neighborhood)

    # Now populate the neighborhoods with households. For this we need the HHID 
    # -> NID mapping:
    for household in households:
        HHID = household.get_ID()
        NEIGHID = HHID_NEIGHID_map[HHID]
        # Get a reference to this neighborhood, and add the household
        neighborhood = Region.get_agent(NEIGHID)
        neighborhood.add_agent(household)

    # Now populate the households with people. For this we need the RESPID -> 
    # HHID mapping and the HHID -> NEIGHID map.
    for person in persons:
        RESPID = person.get_ID()
        HHID = RESPID_HHID_map[RESPID]
        NEIGHID = HHID_NEIGHID_map[HHID]
        # Get a reference to this neighborhood
        neighborhood = Region.get_agent(NEIGHID)
        # Then get a reference to the proper household, and add the person
        household = neighborhood.get_agent(HHID)
        household.add_agent(person)

    return region
