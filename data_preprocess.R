#!/usr/bin/env Rscript
###############################################################################
# This file preprocesses the CVFS data in R and cleans it so that it can be 
# used in initialize.py.
###############################################################################

library("foreign")

###############################################################################
# First handle DS0004 - the census dataset
census <- read.xport("/media/Local_Secure/ICPSR_0538_Restricted/da04538-0004_REST.xpt")
# Exclude neighborhoods 152-172
census <- census[census$NEIGHID <= 151,]
# 5 people don't know their age, coded as -3 in dataset. Exclude these 
# individuals.
census$CENAGE[census$CENAGE==-3] <- NA
# The model runs in months. So convert ages from years to months
AGEMNTHS <- census$CENAGE*12
census.processed <- with(census, data.frame(RESPID, AGEMNTHS, CENGENDR))
census.processed$CENGENDR[census.processed$CENGENDR==1] <- "male"
census.processed$CENGENDR[census.processed$CENGENDR==2] <- "female"
# Eliminate the 5 people with unknown ages, and the 2 other NAs in the dataset
census.processed <- na.omit(census.processed)

###############################################################################
# Now handle DS0012, the individual data, to get desired family size 
# preferences.
t1indiv <- read.xport("/media/Local_Secure/ICPSR_0538_Restricted/da04538-0012_REST.xpt")
# Exclude neighborhoods 152-172
t1indiv <- t1indiv[t1indiv$NEIGHID <= 151,]
columns <- grep('RESPID|F7$', names(t1indiv))
desnumchild <- t1indiv[columns]
names(desnumchild)[2] <- "numchild"
# People who said "it is god's will" were coded as 97, and reasked the 
# question, in F9.
godswill <- which(desnumchild$numchild==97)
desnumchild[godswill,]$numchild <- desnumchild$F9[godswill]
# 2 people said a range from low to high. Here, arbitrarily, take the high 
# number, stored in F7B.
range <- which(desnumchild$numchild==95)
desnumchild[range,]$numchild <- desnumchild$F7B[range]
# 28 people said they don't know. This is coded as -3 in the CVFS data. Recode 
# this as -1.
desnumchild$numchild[desnumchild$numchild==-3] <- -1
# Also recode no response given (NA in the dataset) as -1
desnumchild$numchild[is.na(desnumchild$numchild)] <- -1
# TODO: Also there are 22 individuals with # kids wanted in the thousands...  
# ask Dirgha what these are
desnumchild$numchild[desnumchild$numchild>1000] <- -1

###############################################################################
# Now handle DS0013, the life history calendar data, to get information on what 
# women had births in the past year (so they can start out ineligible for 
# pregnancy).
lhc <- read.xport("/home/azvoleff/Data/CVFS_Public/DS0013/04538-0013-Data.xpt")
# NOTE: lhc contains no NEIGHID column. Respondents in excluded neighborhoods 
# (greather than 151) will be dropped when the lhc data is merged later on in 
# the process.
cols.childL2053 <- grep('^C[0-9]*L2053$', names(lhc))
col.respid <- grep("RESPID", names(lhc))
lhc.child2053 <- reshape(lhc[c(col.respid, cols.childL2053)], direction="long",
        varying=names(lhc[cols.childL2053]), idvar="RESPID", timevar="childnum",
        sep="")
# Count "born" (coded as 1), "born, died in same year" (coded as 5), and "born, 
# lived away 6 months in same year" (coded as 6), as recent births. Recode 
# these three events as 1, code all other events as 0
lhc.child2053$C[lhc.child2053$C==5] <- 1
lhc.child2053$C[lhc.child2053$C==6] <- 1
lhc.child2053$C[lhc.child2053$C!=1] <- 0
lhc.child2053$C[is.na(lhc.child2053$C)] <- 0
recentbirths <- lhc.child2053[lhc.child2053$C==1,]

###############################################################################
# Now handle DS0016 - the household relationship grid. Merge the census data 
# with the relationship grid.
hhrel <- read.xport("/media/Local_Secure/ICPSR_0538_Restricted/da04538-0016_REST.xpt")
# Exclude neighborhoods 152-172
hhrel <- hhrel[hhrel$NEIGHID <= 151,]
hhrel.processed  <- with(hhrel, data.frame(RESPID, HHID, SUBJECT, PARENT1, PARENT2, SPOUSE1, SPOUSE2, SPOUSE3))
hhrel.processed  <- merge(hhrel.processed, census.processed, by="RESPID")

# Merge the desnumchild data for desired family size. Note that I do not have 
# data for all individuals, so individuals for whom I do not have desired 
# family size I will code them as 0.
hhrel.processed <- cbind(hhrel.processed, 
        numchild=matrix(-1, nrow(hhrel.processed), 1))
# Four indiv. in the desnumchild frame are not in the hhrel.processed frame.  
# First remove these 4 indiv from the desnumchild frame.
desnumchild <- desnumchild[-which(!(desnumchild$RESPID %in%
        hhrel.processed$RESPID)),]
hhrel.processed[match(desnumchild$RESPID,
        hhrel.processed$RESPID),]$numchild <- desnumchild$numchild

# Add the recent birth tags onto hhrel.processed
hhrel.processed <- cbind(hhrel.processed, 
        recentbirth=matrix(-1, nrow(hhrel.processed), 1))
hhrel.processed[match(recentbirths$RESPID,
        hhrel.processed$RESPID),]$recentbirth <- recentbirths$recentbirth

###############################################################################
# Now handle DS0002 - the time 1 baseline agriculture data
hhag <- read.xport("/media/Local_Secure/ICPSR_0538_Restricted/da04538-0002_REST.xpt")
# Exclude neighborhoods 152-172
hhag <- hhag[hhag$NEIGHID <= 151,]
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
# Now handle DS0014 - the neighborhood history data
neigh <- read.xport("/media/Local_Secure/ICPSR_0538_Restricted/da04538-0014_REST.xpt")
# Exclude neighborhoods 152-172
neigh <- neigh[neigh$NEIGHID <= 151,]
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
# Now handle the land use data. Import land use data from time 1 for 4 
# different classes, as is done by Axinn (2007). The classes are:
# 	Agricultural vegetation - BARI1, IKHET1, RKHET1
# 	Non-agricultural vegetation - GRASSC1, GRASSP1, PLANTC1, PLANTP1
# 	Private buildings - HHRESID1, MILL1, OTRBLD1
# 	Public buildings - ROAD1, SCHOOL1, TEMPLE1
# 	Other uses - CANAL1, POND1, RIVER1, SILT1, UNDVP1
lu <- read.xport("/media/Local_Secure/ICPSR_SupplementalData/Survey_converted/landuse.xpt")
# Exclude neighborhoods 152-172
lu$NEIGHID <- as.ordered(lu$NEIGHID)
lu <- lu[lu$NEIGHID <= 151,]

land.agveg <- with(lu, rowSums(cbind(BARI1, IKHET1, RKHET1)))
land.nonagveg <- with(lu, rowSums(cbind(GRASSC1, GRASSP1, PLANTC1, PLANTP1)))
land.privbldg <- with(lu, rowSums(cbind(HHRESID1, MILL1, OTRBLD1)))
land.pubbldg <- with(lu, rowSums(cbind(ROAD1, SCHOOL1, TEMPLE1)))
land.other <- with(lu, rowSums(cbind(CANAL1, POND1, RIVER1, SILT1, UNDVP1)))

lu.processed <- data.frame(NEIGHID=lu$NEIGHID, land.agveg, land.nonagveg, land.privbldg, land.pubbldg, land.other)
# Convert land areas expressed in square feet to square meters
lu.processed[2:6]  <- lu.processed[2:6] * .09290304

# Prior to merging, convert factor levels in lu (the NEIGHID column) to 
# numeric, then back to factor, so that neighIDs with less than three 
# characters (like 001) are instead represented as integers (001 -> 1). If this 
# is not done, neighborhoods will be lost as merge will think neighborhood 001 
# in dataframe lu has no complement in the neigh dataframe (where it is 
# represented with a NEIGHID of 1 instead of 001).
lu.processed$NEIGHID <- factor(as.numeric(lu.processed$NEIGHID))

# Join these rows to the neighborhood data processed earlier.
neigh.processed <- merge(neigh.processed, lu.processed, by="NEIGHID")

###############################################################################
# Output data. Data is restricted so it has to be stored in an encrypted 
# folder. Save both Rdata files (to be used for synthetic agent generation) and 
# csv files (for loading into the model).
write.csv(hhrel.processed, file="/media/Local_Secure/ChitwanABM_init/hhrel.csv", row.names=FALSE)
save(hhrel.processed, file="/media/Local_Secure/ChitwanABM_init/hhrel.Rdata")
write.csv(hhag.processed, file="/media/Local_Secure/ChitwanABM_init/hhag.csv", row.names=FALSE)
save(hhag.processed, file="/media/Local_Secure/ChitwanABM_init/hhag.Rdata")
write.csv(neigh.processed, file="/media/Local_Secure/ChitwanABM_init/neigh.csv", row.names=FALSE)
save(neigh.processed, file="/media/Local_Secure/ChitwanABM_init/neigh.Rdata")
