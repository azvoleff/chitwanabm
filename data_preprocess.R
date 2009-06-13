###############################################################################
# This file preprocesses the CVFS data in R and cleans it so that it can be 
# used in initialize.py.
###############################################################################

library("foreign")

###############################################################################
# First handle DS0004 - the census dataset
census <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0004_REST.xpt")
cenage <- census$CENAGE
# 5 people don't know their age, and there are 2 NAs in the dataset
cenage[cenage==-3] <- NA
cenage <- na.omit(cenage)
census.processed <- data.frame(CENAGE=cenage)

###############################################################################
# Now handle DS0016 - the household relationship grid
hhrel <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0016_REST.xpt")

###############################################################################
# Now handle DS0002 - the time 1 baseline agriculture data
hhag <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0002_REST.xpt")

###############################################################################
# Now handle DS0014 - the neighborhoods history data
neigh <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0014_REST.xpt")
# Axinn (2007) uses the "average number of years non-family services were 
# within a 30 minute walk". The data are stored for each service for each year, 
# using Nepali years. For example, SCHLFT10 for a particular neighborhood 
# stores the number of minutes on foot to walk to the nearest school from that 
# neighborhood for that year (the '10' represents Nepali year 2010, which is 
# 1953/1954 in Western years).
neigh_ID <- neigh$NEIGHID
services <- neigh[grep('SCHLFT|HLTHFT|BUSFT|MARFT|^EMPFT', names(neigh))]
# services currently expresses the number of minutes on foot to get each 
# service for each year. Convert it so it is 1 if services were <= 30 minutes 
# walk away, and 0 otherwise
services[services<=30] <- 1
services[services>30] <- 0
avg_yrs_services <- rowSums(services) / 5
# Find if electricity is currently available in the neighborhood (as of the 
# census)
elec_avail <- as.logical(neigh$ELEC52)
neigh.processed <- data.frame(NEIGHID=neigh_ID, AVG_YRS_SRVC=avg_yrs_services, ELEC_AVAIL=elec_avail)


###############################################################################
# Output data. Data is restricted so it has to be stored in an encrypted 
# folder.
