"""
Part of Chitwan Valley (non-spatial) agent-based model.

Sets up a CV_ABM_NS model run: Initializes neighborhood/household/person agents 
and land use based on a set of distributions for the value of particular 
characteristics for each agent.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

from chitwanABM.agents import Person, Household, Neighborhood

def read_census(textfile):
def read_household_relationships(textfile):
    relations = {}

    return relations

def assemble_agents(relationshipsFile, censusFile):
    """Reads data in from the CVFS census (dataset DS0003 (public) or 
    DS0004 (restricted)) and from the household relationship grid, CVFS 
    dataset DS0015 (public) or DS0016 (restricted), and assembles person, 
    household, neighborhood, and region agents."""
    relations = read_CVFS_Data(relationshipsFile) 
    census = read_CVFS_Data(censusFile) 

    chitwan = Region()

    # First sort the relations data into households (not instances of the 
    # households class, but rather a dictionary keyed by NID where the 
    # values are lists of the raw relations data for all persons sharing that 
    # household ID
    household_sets = {}
    for PID in relations.iterkeys():
        # Get the HID of this persons household
        HID = int(relations[PID]['HHID'])
        # Now store this person in a list of people for that household
        if household_sets.has_key(HID):
            household_sets[HID].append(relations[PID])
        else:
            household_sets[HID] = relations[PID]
   
    # For each household, create a SUBJECT -> RESPID mapping. For example:
    # dictionary[HHID][SUBJECT] = RESPID (Remember that RESPID is same as PID)
    RESPID_dict= {}
    for HID in household_sets.iterkeys():
        household_set = household_sets[HID]
        for PID in household_set.iterkeys():
            relation = household_set[PID]
            SUBJECT = int(relation['SUBJECT'])
            RESPID_dict[HID][SUBJECT] = RESPID

    # Now convert the references to subject IDs in the household_sets to 
    # reference PIDs (same thing as RESPIDs).
    for HID in household_sets.iterkeys():
        household_set = household_sets[HID]
        for PID in household_set.iterkeys():

    # Loop over all agents in the relationship grid. PID here is the same thing 
    # as RESPID in the CVFS data
    for PID in relations.iterkeys():
        # Get the agents sex and age from the census data
        CENAGE = int(census[PID]['CENAGE'])
        CENGENDR = census[PID]['CENGENDR']

        newPerson = Person(birthdate=None, age=CENAGE, sex=CENGENDR)

        respondentrelations = relations[PID]

    return region
    
def read_CVFS_data(textfile):
    """Reads in CVFS data from a CSV file into a nested dictionary object, 
    where the first column of the file is a unique key, and the first line of 
    the file gives the column headings (used as keys within the nested 
    dictionary object). No conversion of the fields is done: they are all 
    stored as strings."""

    try:
        file = open(textfile, 'r')
        lines = file.readlines()
        file.close()
    except:
        raise IOError("error reading %S"%(textfile))
     

    firstline = lines[0].strip('\n').split(', ')
    keyfieldName = firstline[0] # This isn't used anywhere
    columnNames = firstline[1:]

    data = {}

    for line in lines[1:]:
        fields = line.strip('\n').split(', ')
        print fields
        data[fields[0]] = {} 
        for field, columnName in zip(fields[1:], columnNames):
            data[fields[0]][columnName] = field

    return data
