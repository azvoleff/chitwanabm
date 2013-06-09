#!/usr/bin/env Rscript
#
# Copyright 2008-2013 Alex Zvoleff
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
# Contact Alex Zvoleff in the Department of Geography at San Diego State 
# University with any comments or questions. See the README.txt file for 
# contact information.

###############################################################################
# This file preprocesses the CVFS data in R and cleans it so that it can be 
# used in initialize.py.
###############################################################################

require(foreign, quietly=TRUE)

RAW_DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
PROCESSED_DATA_PATH <- commandArgs(trailingOnly=TRUE)[2]
RANDOM_SEED <- commandArgs(trailingOnly=TRUE)[3]

if (is.na(RAW_DATA_PATH)) stop("Raw data path must be supplied")
if (is.na(PROCESSED_DATA_PATH)) stop("Processed data path must be supplied")

if (is.na(RANDOM_SEED)) stop("Random seed must be supplied")
set.seed(RANDOM_SEED)

# Define a function to replace NAs with resampling:
replace_nas <- function(input_vector) {
    na_loc <- is.na(input_vector)
    input_vector[na_loc] <- sample(input_vector[!na_loc], sum(na_loc), replace=TRUE)
    return(input_vector)
}

###############################################################################
# First handle DS0004 - the census dataset
census <- read.xport(paste(RAW_DATA_PATH, "da04538-0004_REST.xpt", sep="/"))
# Exclude neighborhoods 152-172
census <- census[census$NEIGHID <= 151,]
# Convert IDs to new 9 digit format:
old_respID_census <- sprintf("%07i", census$RESPID)
census$NEIGHID <- sprintf("%03i", as.numeric(substr(old_respID_census, 1, 3)))
HHNUM_census <- sprintf("%03i", as.numeric(substr(old_respID_census, 4, 5)))
census$HHID <- paste(census$NEIGHID, HHNUM_census, sep="")
SUBJID_census <- sprintf("%03i", as.numeric(substr(old_respID_census, 6, 7)))
census$RESPID <- paste(census$HHID, SUBJID_census, sep="")
# 5 people don't know their age, coded as -3 in dataset. Exclude these 
# individuals.
census$CENAGE[census$CENAGE==-3] <- NA
# The model runs in months. So convert ages from years to months
AGEMNTHS <- census$CENAGE*12
# Randomize ages so birthdates are evenly distributed throughout the year:
AGEMNTHS <- AGEMNTHS + floor(runif(length(AGEMNTHS), -11, 0))
census.processed <- with(census, data.frame(RESPID, AGEMNTHS, CENGENDR))
census.processed$CENGENDR[census.processed$CENGENDR==1] <- "male"
census.processed$CENGENDR[census.processed$CENGENDR==2] <- "female"
# Eliminate the 5 people with unknown ages, and the 2 other NAs in the dataset
census.processed <- na.omit(census.processed)

###############################################################################
# Now handle DS0012, the individual data, to get desired family size 
# preferences and educational histories.
t1indiv <- read.xport(paste(RAW_DATA_PATH, "da04538-0012_REST.xpt", sep="/"))
# Exclude neighborhoods 152-172
t1indiv <- t1indiv[t1indiv$NEIGHID <= 151,]
# Convert IDs to new 9 digit format:
old_respID_t1indiv <- sprintf("%07i", t1indiv$RESPID)
t1indiv$NEIGHID <- sprintf("%03i", as.numeric(substr(old_respID_t1indiv, 1, 3)))
HHNUM_t1indiv <- sprintf("%03i", as.numeric(substr(old_respID_t1indiv, 4, 5)))
t1indiv$HHID <- paste(t1indiv$NEIGHID, HHNUM_t1indiv, sep="")
SUBJID_t1indiv <- sprintf("%03i", as.numeric(substr(old_respID_t1indiv, 6, 7)))
t1indiv$RESPID <- paste(t1indiv$HHID, SUBJID_t1indiv, sep="")

desnumchild <- t1indiv[grep('^(RESPID|F7)$', names(t1indiv))]
names(desnumchild)[names(desnumchild) == "F7"] <- "desnumchild"
# People who said "it is god's will" were coded as 97, and reasked the 
# question, in F9.
godswill <- which(desnumchild$desnumchild==97)
desnumchild[godswill,]$desnumchild <- t1indiv$F9[godswill]
# Some still didn't give an answer - recode this person as NA
godswill <- which(desnumchild$desnumchild==97)
desnumchild[godswill,]$desnumchild <- NA
# 2 people said a range from low to high. Here, take an average of the low and 
# high number, stored in F7A and F7B.
# TODO: Fix this:
child_range <- which(desnumchild$desnumchild==95)
desnumchild[child_range,]$desnumchild <- t1indiv$F7B[child_range]
#desnumchild[child_range,]$desnumchild <- desnumchild$F7A[child_range] / desnumchild$F7B[child_range]
# 28 people said they don't know. This is coded as -3 in the CVFS data. Recode 
# this as NA so it will get replaced when it is resampled.
desnumchild$desnumchild[desnumchild$desnumchild==-3] <- NA

# Now get years schooling data
schooling_col <- grep('^A1$', names(t1indiv))
schooling <- t1indiv[schooling_col]
names(schooling) <- "schooling"
# Leave schooling coded as years of schooling
schooling <- cbind(RESPID=t1indiv$RESPID, schooling)

# Now get childhood community context data. Below are the variables for 
# non-family services w/in a 1 hour walk at age 12.
# 	school D2
# 	health D8
# 	bus D12
# 	employer D16
# 	markey D22
cc_cols <- grep('^(D2|D8|D12|D16|D22)$', names(t1indiv))
ccchild <- t1indiv[cc_cols]
names(ccchild)[grep('^D2$', names(ccchild))] <- "child_school_1hr"
names(ccchild)[grep('^D8$', names(ccchild))] <- "child_health_1hr"
names(ccchild)[grep('^D12$', names(ccchild))] <- "child_bus_1hr"
names(ccchild)[grep('^D16$', names(ccchild))] <- "child_emp_1hr"
names(ccchild)[grep('^D22$', names(ccchild))] <- "child_market_1hr"
ccchild[ccchild < 0] <- NA # these will be replaced later by resampling
ccchild <- cbind(RESPID=t1indiv$RESPID, ccchild)

# Now get parent's characteristics data:
# parent's contraceptive use
# I17 father's work
# I11 father school (ever)
# I12 father school (years)
# I15 mother's work
# I7 mother school (ever)
# I8 mother school (years)
# I19 mother's number of children
# I21 parents birth control ever
parents_char_cols <- grep('^(I17|I11|I12|I15|I19|I21|I7|I8)$', names(t1indiv))
parents_char <- t1indiv[parents_char_cols]
names(parents_char)[grep('^I17$', names(parents_char))] <- "father_work"
names(parents_char)[grep('^I11$', names(parents_char))] <- "father_school_ever"
names(parents_char)[grep('^I12$', names(parents_char))] <- "father_years_schooling"
names(parents_char)[grep('^I15$', names(parents_char))] <- "mother_work"
names(parents_char)[grep('^I19$', names(parents_char))] <- "mother_num_children"
names(parents_char)[grep('^I21$', names(parents_char))] <- "parents_contracep_ever"
names(parents_char)[grep('^I7$', names(parents_char))] <- "mother_school_ever"
names(parents_char)[grep('^I8$', names(parents_char))] <- "mother_years_schooling"

# People who responded no to question I7 (mother never went to school) are 
# coded as -1 for I8 (years went to school). Set these people's mothers to 0.  
parents_char$mother_years_schooling[parents_char$mother_school_ever == 0] <- 0
# Same goes for the father schooling coding.
parents_char$father_years_schooling[parents_char$father_school_ever == 0] <- 0

parents_char[parents_char < 0] <- NA # will be replaced with resampling
parents_char <- cbind(RESPID=t1indiv$RESPID, parents_char)

parents_char$mother_years_schooling <- replace_nas(parents_char$mother_years_schooling)
parents_char$father_years_schooling <- replace_nas(parents_char$father_years_schooling)

###############################################################################
# Now handle DS0013, the life history calendar data, to get information on what 
# women had births in the past year (so they can start out ineligible for 
# pregnancy).
lhc <- read.xport(paste(RAW_DATA_PATH, "04538_0013_data.xpt", sep="/"))
# NOTE: lhc contains no NEIGHID column before I add one here.
# Convert IDs to new 9 digit format:
old_respID_lhc <- sprintf("%07i", lhc$RESPID)
lhc$NEIGHID <- sprintf("%03i", as.numeric(substr(old_respID_lhc, 1, 3)))
HHNUM_lhc <- sprintf("%03i", as.numeric(substr(old_respID_lhc, 4, 5)))
lhc$HHID <- paste(lhc$NEIGHID, HHNUM_lhc, sep="")
SUBJID_lhc <- sprintf("%03i", as.numeric(substr(old_respID_lhc, 6, 7)))
lhc$RESPID <- paste(lhc$HHID, SUBJID_lhc, sep="")
lhc <- lhc[lhc$NEIGHID <= 151,]
cols.childL2053 <- grep('^C[0-9]*L2053$', names(lhc))
recent_birth <- lhc[cols.childL2053]
# Count "born" (coded as 1), "born, died in same year" (coded as 5), and "born, 
# lived away 6 months in same year" (coded as 6), as recent births. Recode 
# these three events as 1, code all other events as 0.
recent_birth[recent_birth == 5] <- 1
recent_birth[recent_birth == 6] <- 1
recent_birth[recent_birth != 1] <- 0
recent_birth[is.na(recent_birth)] <- 0
# Now add up across the rows - anything greater than or equal to 1 means there 
# was (at least) one birth in year 2053.
recent_birth <- apply(recent_birth, 1, sum, na.rm=TRUE)
recent_birth[recent_birth > 1] <- 1

# Also add a "number of children" variable to each person, by counting up the
# counting the number of entries in the SEXC1-SEXC15 columns for each person.
sexc_cols <- grep('SEXC[1]?[0-9]', names(lhc))
n_children <- apply(!is.na(lhc[sexc_cols]), 1, sum)

# Set marriage time to the time of the most recent marriage (some may have had 
# more than one marriage).
lhc_marr_cols <- grep('^(M[1]?[0-9]E199[4-9])|(M[1]?[0-9]E20[0-5][0-9])$', names(lhc))

marr_year <- apply(lhc[lhc_marr_cols], 1,
                    function(marit_row) match(1, rev(marit_row)))
marr_year <- 1996.5 - (marr_year %% 60)
# We only have the month of marriage for the first spouse, so subtract a random 
# number from 1-12 from each marr_year
marr_date <- marr_year + sample(seq(1,12)/12, length(marr_year), replace=TRUE)

lhc_marr_exists_cols <- grep('^(MYN[1]?[0-9])$', names(lhc))
ever_had_spouse <- apply(lhc[lhc_marr_exists_cols], 1,
                    function(marit_row) sum(marit_row, na.rm=T)==1)

lhc_recode <- data.frame(RESPID=lhc$RESPID, recent_birth, n_children, marr_date, ever_had_spouse)

###############################################################################
# Now handle DS0016 - the household relationship grid. Merge the census data 
# with the relationship grid.
hhrel <- read.xport(paste(RAW_DATA_PATH, "da04538-0016_REST.xpt", sep="/"))
# Exclude neighborhoods 152-172
hhrel <- hhrel[hhrel$NEIGHID <= 151,]
# Convert IDs to new 9 digit format:
old_respID_hhrel <- sprintf("%07i", hhrel$RESPID)
hhrel$NEIGHID <- sprintf("%03i", as.numeric(substr(old_respID_hhrel, 1, 3)))
HHNUM_hhrel <- sprintf("%03i", as.numeric(substr(old_respID_hhrel, 4, 5)))
hhrel$HHID <- paste(hhrel$NEIGHID, HHNUM_hhrel, sep="")
SUBJID_hhrel <- sprintf("%03i", as.numeric(substr(old_respID_hhrel, 6, 7)))
hhrel$RESPID <- paste(hhrel$HHID, SUBJID_hhrel, sep="")
hhrel.processed  <- with(hhrel, data.frame(RESPID, HHID, SUBJECT, PARENT1, PARENT2, SPOUSE1, SPOUSE2, SPOUSE3))
hhrel.processed  <- merge(hhrel.processed, census.processed, by="RESPID")

#TODO: Get these fixed in the original CVFS dataset.
# Fix the incorrect SPOUSE2 variable for one respondent.
hhrel.processed[hhrel.processed$RESPID=="151003002",]$SPOUSE2 <- 4
# Also fix the incorrect SPOUSE1 variables for two other respondents.
hhrel.processed[hhrel.processed$RESPID=="035002001",]$SPOUSE1 <- 2
hhrel.processed[hhrel.processed$RESPID=="035002002",]$SPOUSE1 <- 1

# Merge the desnumchild data for desired family size. Note that I do not have 
# data for all individuals, so individuals for whom I do not have desired 
# family size I will use resampling to assign values.
hhrel.processed <- merge(hhrel.processed, desnumchild, all.x=TRUE)
hhrel.processed$desnumchild <- replace_nas(hhrel.processed$desnumchild)

# Add the recent birth tags and number of children count onto hhrel.processed
hhrel.processed <- merge(hhrel.processed, lhc_recode, all.x=TRUE)
# Only replace NAs in recent birth and n_children for ever-married individuals 
# over age 15. Otherwise set recent birth to 0 and n_children to 0.
had_spouse <- hhrel.processed$ever_had_spouse == 1
had_spouse[is.na(had_spouse)] <- FALSE
under_15 <- hhrel.processed$AGEMNTHS < (15*12)
hhrel.processed[had_spouse, ]$recent_birth <- replace_nas(hhrel.processed[had_spouse, ]$recent_birth)
hhrel.processed[under_15 | !had_spouse, ]$recent_birth <- 0
hhrel.processed[had_spouse, ]$n_children <- replace_nas(hhrel.processed[had_spouse, ]$n_children)
hhrel.processed[under_15 | !had_spouse, ]$n_children <- 0

# Merge the education data
hhrel.processed <- merge(hhrel.processed, schooling, all.x=TRUE)
hhrel.processed$schooling <- replace_nas(hhrel.processed$schooling)

# Merge the childhood non-family services data
hhrel.processed <- merge(hhrel.processed, ccchild, all.x=TRUE)
child_cols <- grep("child_", names(hhrel.processed))
hhrel.processed[child_cols] <- apply(hhrel.processed[child_cols], 2, replace_nas)

# Merge the parent's characteristics data
hhrel.processed <- merge(hhrel.processed, parents_char, all.x=TRUE)
parents_char_cols <- grep("^(father_work|father_years_schooling|mother_work|mother_years_schooling|mother_num_children|parents_contracep_ever)$", names(hhrel.processed))
hhrel.processed[parents_char_cols] <- apply(hhrel.processed[parents_char_cols], 2, replace_nas)

###############################################################################
# Now handle DS0002 - the time 1 baseline agriculture data
hhag <- read.xport(paste(RAW_DATA_PATH, "da04538-0002_REST.xpt", sep="/"))
# Exclude neighborhoods 152-172
hhag <- hhag[hhag$NEIGHID <= 151,]
# Convert IDs to new 6 digit format:
old_hhID_hhag <- sprintf("%05i", hhag$HHID)
hhag$NEIGHID <- sprintf("%03i", as.numeric(substr(old_hhID_hhag, 1, 3)))
HHNUM_hhag <- sprintf("%03i", as.numeric(substr(old_hhID_hhag, 4, 5)))
hhag$HHID <- paste(hhag$NEIGHID, HHNUM_hhag, sep="")
# Calculate total livestock units
chickduck_1996<- hhag$BAB2
pigeons_1996 <- hhag$BAB3
bulls_1996 <- hhag$BAB5
cows_1996 <- hhag$BAB6
hebuff_1996<- hhag$BAB7
shebuff_1996 <- hhag$BAB8
sheep_goats_1996 <- hhag$BAB9
pigs_1996 <- hhag$BAB10
chickduck_1996[chickduck_1996 == -1] <- 0
pigeons_1996[pigeons_1996 == -1] <- 0
bulls_1996[bulls_1996 == -1] <- 0
cows_1996[cows_1996 == -1] <- 0
hebuff_1996[hebuff_1996 == -1] <- 0
shebuff_1996[shebuff_1996 == -1] <- 0
sheep_goats_1996[sheep_goats_1996 == -1] <- 0
pigs_1996[pigs_1996 == -1] <- 0
hhag$TLU_birds_1996 <- chickduck_1996 * .01 # chickens and ducks_1996
hhag$TLU_birds_1996 <- hhag$TLU_birds_1996 + pigeons_1996 * .01 # pigeons
hhag$TLU_livestock_1996 <- bulls_1996 *.5 # bullock_1996s
hhag$TLU_livestock_1996 <- hhag$TLU_livestock_1996 + cows_1996 * .5 # cows
hhag$TLU_livestock_1996 <- hhag$TLU_livestock_1996 + hebuff_1996 * .5 # he buffaloes
hhag$TLU_livestock_1996 <- hhag$TLU_livestock_1996 + shebuff_1996 * .5 # she buffaloes
hhag$TLU_livestock_1996 <- hhag$TLU_livestock_1996 + sheep_goats_1996 * .1 # sheep and goats
hhag$TLU_livestock_1996 <- hhag$TLU_livestock_1996 + pigs_1996 * .2 # pigs
hhag$TLU_birds_1996[is.na(hhag$TLU_birds_1996)] <- 0
hhag$TLU_livestock_1996[is.na(hhag$TLU_livestock_1996)] <- 0
hhag$TLU_all_1996 <- hhag$TLU_birds_1996 + hhag$TLU_livestock_1996
hhag$TLU_all_restrict_1996 <- hhag$TLU_all_1996
hhag$TLU_all_restrict_1996[hhag$TLU_all_restrict_1996 > 15] <- 15
# Did household do any farming?
hhag$any_farming_1996 <- hhag$BAA1
# Wealth measures
hhag$own_radio_1996 <- hhag$BAC1
hhag$own_TV_1996 <- hhag$BAC3
hhag$own_bike_1996 <- hhag$BAC5
hhag$own_motorbike_1996 <- hhag$BAC7
hhag$own_cart_1996 <- hhag$BAC9
hhag$own_total_1996 <- rowSums(cbind(hhag$own_radio_1996,
                                     hhag$own_TV_1996,
                                     hhag$own_bike_1996,
                                     hhag$own_motorbike_1996,
                                     hhag$own_cart_1996))
hhag.processed <- with(hhag, data.frame(HHID, NEIGHID, BAA10A, BAA18A, BAA43, 
                                        BAA44, TLU_all_1996, any_farming_1996, 
                                        own_total_1996))
# Need to handle households where questions BAA10A and BAA18A were 
# innappropriate (where they did no farming on that type of land).
hhag.processed$BAA10A[hhag.processed$BAA10A==1] <- TRUE
hhag.processed$BAA10A[hhag.processed$BAA10A!=1] <- FALSE
hhag.processed$BAA18A[hhag.processed$BAA18A==1] <- TRUE
hhag.processed$BAA18A[hhag.processed$BAA18A!=1] <- FALSE
hhag.processed$BAA43[hhag.processed$BAA43==1] <- TRUE
hhag.processed$BAA43[hhag.processed$BAA43!=1] <- FALSE
# Only include individuals in hhrel that are in households for which hhag 
# information is available:
in_hhag <- which(hhrel.processed$HHID %in% hhag.processed$HHID)
hhrel.processed <- hhrel.processed[in_hhag,]

###############################################################################
# Now handle DS0014 - the neighborhood history data
neigh <- read.xport(paste(RAW_DATA_PATH, "da04538-0014_REST.xpt", sep="/"))
# Exclude neighborhoods 152-172
neigh <- neigh[neigh$NEIGHID <= 151,]
# Convert IDs to new 3 digit format:
old_neighID <- sprintf("%03i", neigh$NEIGHID)
neigh$NEIGHID <- sprintf("%03i", as.numeric(substr(old_neighID, 1, 3)))
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
services_lt15 <- services
services_lt15[services_lt15<=15] <- 1
services_lt15[services_lt15>15] <- 0
avg_yrs_services_lt15 <- rowSums(services_lt15) / 5
services_lt30 <- services
services_lt30[services_lt30<=30] <- 1
services_lt30[services_lt30>30] <- 0
avg_yrs_services_lt30 <- rowSums(services_lt30) / 5
# Find if electricity is currently available in the neighborhood (as of the 
# census)
elec_avail <- neigh$ELEC52
# Get total number of community groups in 1996 in each neighborhood
neigh_grps_var_names <- paste(c('NEIGHID',
                              'GRPWMN52',
                              'GRPUSR52',
                              'SFMRG52',
                              'GRPOTR52'), collapse='|')
neigh_grps_cols <- grep(paste('^(', neigh_grps_var_names, ')$', sep=''), names(neigh))
neigh_grps_vars <- neigh[neigh_grps_cols]
# TODO: Check with Dirgha why there are so many missing values for number of 
# community groups in the neighborhood history dataset for T1
neigh_grps_vars[is.na(neigh_grps_vars)] <- 0
num_groups_1996 <- rowSums(with(neigh_grps_vars, cbind(GRPWMN52, GRPUSR52, 
                                                       SFMRG52, GRPOTR52)))

# Calculate the distance of each neighborhood from Narayanghat (using the 
# coordinates of the center of the road in the middle of the downtown area of 
# Narayanghat).
dist_narayanghat <- sqrt((neigh$NX - 245848)**2 + (neigh$NY - 3066013)**2)
# Now convert from meters to kilometers
dist_narayanghat <- (dist_narayanghat / 1000)

neigh.processed <- data.frame(NEIGHID=neigh_ID, avg_yrs_services_lt15, 
                              avg_yrs_services_lt30, 
                              num_groups=num_groups_1996, 
                              ELEC_AVAIL=elec_avail, X=neigh$NX, Y=neigh$NY, 
                              dist_nara=dist_narayanghat)
# Merge the 1996 non-family services data.  Below are the variables for 
# non-family services w/in a 1 hour walk at age 12.
# 	school SCHLFT52
# 	health HLTHFT52
# 	bus BUSFT52
# 	employer EMPFT52
# 	market MARFT52
nonfam1996_cols<- grep('^(NEIGHID|SCHLFT52|HLTHFT52|BUSFT52|EMPFT52|MARFT52)$', names(neigh))
ccadult <- neigh[nonfam1996_cols]
neigh.processed <- merge(neigh.processed, ccadult)

###############################################################################
# Now handle the land use data. Import land use data from time 1 and make 5 
# different classes, as is done by Axinn (2007). The classes are:
# 	Agricultural vegetation - BARI1, IKHET1, RKHET1
# 	Non-agricultural vegetation - GRASSC1, GRASSP1, PLANTC1, PLANTP1
# 	Private buildings - HHRESID1, MILL1, OTRBLD1
# 	Public buildings - ROAD1, SCHOOL1, TEMPLE1
# 	Other uses - CANAL1, POND1, RIVER1, SILT1, UNDVP1
lu <- read.xport(paste(RAW_DATA_PATH, "landuse.xpt", sep="/"))
# Convert IDs to new 3 digit format:
old_neighID <- sprintf("%03i", lu$NEIGHID)
lu$NEIGHID <- sprintf("%03i", as.numeric(substr(old_neighID, 1, 3)))
# Exclude neighborhoods 152-172
lu <- lu[lu$NEIGHID <= 151,]

land.agveg <- with(lu, rowSums(cbind(BARI1, IKHET1, RKHET1)))
land.nonagveg <- with(lu, rowSums(cbind(GRASSC1, GRASSP1, PLANTC1, PLANTP1)))
land.privbldg <- with(lu, rowSums(cbind(HHRESID1, MILL1, OTRBLD1)))
land.pubbldg <- with(lu, rowSums(cbind(ROAD1, SCHOOL1, TEMPLE1)))
land.other <- with(lu, rowSums(cbind(CANAL1, POND1, RIVER1, SILT1, UNDVP1)))

lu.processed <- data.frame(NEIGHID=lu$NEIGHID, land.agveg, land.nonagveg, land.privbldg, land.pubbldg, land.other)
# Convert land areas expressed in square feet to square meters
lu.processed[2:6]  <- lu.processed[2:6] * .09290304

# Join these rows to the neighborhood data processed earlier.
neigh.processed <- merge(neigh.processed, lu.processed, by="NEIGHID")

###############################################################################
# Add on forest distances rows:
forest_distances <- read.csv(paste(RAW_DATA_PATH, "CVFS_NBHs_forest_distances_recode.csv", sep="/"))
columns <- grep('^(NEIGHID)|(BZ_meters)|(CNP_meters)|(closest_type)|(closest_meters)$', names(forest_distances))
forest_distances <- forest_distances[columns]
forest_distances$NEIGHID <- sprintf("%03i", as.numeric(substr(forest_distances$NEIGHID, 1, 3)))
neigh.processed <- merge(neigh.processed, forest_distances, by="NEIGHID")

###############################################################################
# Add on rates of change of NFO distance in minutes on foot.
nfo_change_rates <- read.csv(paste(RAW_DATA_PATH, "NFO_change_mean_annual_minft.csv", sep="/"))
nfo_change_rates$NEIGHID <- factor(sprintf("%03i", as.numeric(nfo_change_rates$NEIGHID)))
change_cols <- !grepl('NEIGHID', names(nfo_change_rates))
# Convert the annual rates to monthly rates.
nfo_change_rates[change_cols] <- nfo_change_rates[change_cols] / 12
neigh.processed <- merge(neigh.processed, nfo_change_rates)

###############################################################################
# Read in the household registry data to get the ethnicities
load(paste(RAW_DATA_PATH, "hhreg.Rdata", sep="/"))
# Convert IDs to new 9 digit format:
old_respID_hhreg <- sprintf("%07i", hhreg$respid)
NEIGHID_hhreg <- sprintf("%03i", as.numeric(substr(old_respID_hhreg, 1, 3)))
HHNUM_hhreg <- sprintf("%03i", as.numeric(substr(old_respID_hhreg, 4, 5)))
SUBJID_hhreg <- sprintf("%03i", as.numeric(substr(old_respID_hhreg, 6, 7)))
hhreg$respid <- paste(NEIGHID_hhreg, HHNUM_hhreg, SUBJID_hhreg, sep="")
# Now get the two needed columns:
columns <- grep('^(respid|ethnic)$', names(hhreg))
hhreg <- hhreg[columns]
names(hhreg)[grep('^respid$', names(hhreg))] <- 'RESPID'
names(hhreg)[grep('^ethnic$', names(hhreg))] <- 'ETHNIC'
# Drop "other" ethnicity for consistency with Massey et al. (2010)
hhreg <- hhreg[!(hhreg$ETHNIC==6),]
hhrel.processed <- merge(hhrel.processed, hhreg)
# One individual has an ethnicity of NA, fix this.
hhrel.processed$ETHNIC <- replace_nas(hhrel.processed$ETHNIC)

###############################################################################
# Output data. Data is restricted so it has to be stored in an encrypted 
# folder. Save both Rdata files (to be used for synthetic agent generation) and 
# csv files (for loading into the model).
write.csv(hhrel.processed, file=paste(PROCESSED_DATA_PATH, "hhrel.csv", sep="/"), row.names=FALSE)
save(hhrel.processed, file=paste(PROCESSED_DATA_PATH, "hhrel.Rdata", sep="/"))
write.csv(hhag.processed, file=paste(PROCESSED_DATA_PATH, "hhag.csv", sep="/"), row.names=FALSE)
save(hhag.processed, file=paste(PROCESSED_DATA_PATH, "hhag.Rdata", sep="/"))
write.csv(neigh.processed, file=paste(PROCESSED_DATA_PATH, "neigh.csv", sep="/"), row.names=FALSE)
save(neigh.processed, file=paste(PROCESSED_DATA_PATH, "neigh.Rdata", sep="/"))

# Save copies of the neighborhoods coordinates and EVI data to the temp path
neigh_coords <- read.csv(paste(RAW_DATA_PATH, "neigh_coords.csv", sep="/"))
write.csv(neigh_coords, file=paste(PROCESSED_DATA_PATH, "neigh_coords.csv", sep="/"), row.names=FALSE)
EVI_data <- read.csv(paste(RAW_DATA_PATH, "Chitwan_NBH_EVI_data.csv", sep="/"))
write.csv(EVI_data, file=paste(PROCESSED_DATA_PATH, "Chitwan_NBH_EVI_data.csv", sep="/"), row.names=FALSE)
