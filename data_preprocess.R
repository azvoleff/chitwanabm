###############################################################################
# This file preprocesses the CVFS data in R and cleans it so that it can be 
# used in initialize.py.
###############################################################################

library("foreign")

###############################################################################
# First handle DS0004 - the census dataset
census <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0004_REST.xpt")
# 5 people don't know their age, coded as -3 in dataset
census$CENAGE[census$CENAGE==-3] <- NA
# The model runs in months. So convert ages from years to months
AGEMNTHS <- census$CENAGE*12
census.processed <- with(census, data.frame(RESPID, AGEMNTHS, CENGENDR))
census.processed$CENGENDR[census.processed$CENGENDR==1] <- "male"
census.processed$CENGENDR[census.processed$CENGENDR==2] <- "female"
# Eliminate the 5 people with unknown ages, and the 2 other NAs in the dataset
census.processed <- na.omit(census.processed)

###############################################################################
# Now handle DS0016 - the household relationship grid. Merge the census data 
# with the relationship grid.
hhrel <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0016_REST.xpt")
hhrel.processed  <- with(hhrel, data.frame(RESPID, HHID, SUBJECT, PARENT1, PARENT2, SPOUSE1, SPOUSE2, SPOUSE3))
hhrel.processed  <- merge(hhrel.processed, census.processed, by="RESPID")

###############################################################################
# Now handle DS0002 - the time 1 baseline agriculture data
hhag <- read.xport("/media/Restricted/Data/ICPSR_0538_Restricted/da04538-0002_REST.xpt")
hhag.processed <- with(hhag, data.frame(HHID, NEIGHID, BAA10A, BAA18A, BAA43, BAA44))
# Need to handle households where questions BAA10A and BAA18A were 
# innappropriate (where they did no farming on that type of land).
hhag.processed$BAA10A[hhag.processed$BAA10A==1] <- TRUE
hhag.processed$BAA10A[hhag.processed$BAA10A!=1] <- FALSE
hhag.processed$BAA18A[hhag.processed$BAA18A==1] <- TRUE
hhag.processed$BAA18A[hhag.processed$BAA18A!=1] <- FALSE

# Only include individuals in hhrel that are in households for which hhag 
# information is available:
in_hhag <- which(hhrel.processed$HHID %in% hhag.processed$HHID)
hhrel.processed <- hhrel.processed[in_hhag,]

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
write.csv(hhrel.processed, file="/media/Restricted/Data/chitwanABM_init_data/hhrel.csv", row.names=FALSE)
write.csv(hhag.processed, file="/media/Restricted/Data/chitwanABM_init_data/hhag.csv", row.names=FALSE)
write.csv(neigh.processed, file="/media/Restricted/Data/chitwanABM_init_data/neigh.csv", row.names=FALSE)
