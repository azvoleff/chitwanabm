#!/usr/bin/env Rscript
###############################################################################
# Loads deaths and age at death from the ICPSR Restricted dataset DS0010, the 
# household registry data, and calculates several statistics (birth rates, 
# marriage rates, and mortality rates) for parameterizing the ChitwanABM model.
###############################################################################

# Hmisc is needed as hhreg is a "labelled" dataframe. If Hmisc is nto included, 
# will get errors saying "cannot coerce class "labelled" into a data.frame"
require(Hmisc, quietly=TRUE)
require(ggplot2, quietly=TRUE)

load("/media/Local_Secure/CVFS_R_format/hhreg.Rdata")
hhreg$gender <- factor(hhreg$gender, labels=c("male", "female"))

# TODO: Need to only consider neighborhoods with neighid < 151

# Function to write out probabilities of events in the format required by the 
# ChitwanABM model.
make.txthazard <- function(probs, binlims, param.name) {
    # param.name is the name used by the ChitwanABM model for this parameter.
    txthazard <- paste("'", param.name, "' : [{", sep="")
    for (rownum in 1:length(probs)) {
        txthazard <- paste(txthazard, "(", binlims[rownum], ", ",
                binlims[rownum+1], "):", round(probs[rownum], digits=4),
                sep="")
        if (rownum<length(probs)) txthazard <- paste(txthazard, ", ", sep="")
    }
    txthazard <- paste(txthazard, "} | validate_hazard(", binlims[1], ", ",
            binlims[length(binlims)], ")]", sep="")
    return(txthazard)
}

make.txtprob <- function(probs, binlims, param.name) {
    # param.name is the name used by the ChitwanABM model for this parameter.
    binlims <- paste(round(binlims, digits=4), collapse=", ")
    probs <- paste(round(probs, digits=4), collapse=", ")
    txtprob <- paste("'", param.name, "' : [((", binlims, "), (", probs,  "))] | validate_prob_dist]", sep="")
    return(txtprob)
}

plot.hazard <- function(probs, plottitle, plotfile) {
    qplot(bin, prob, geom="line", xlab="Age (years)",
            ylab="Annual probability", main=plottitle, data=probs)
    ggsave(plotfile, width=8.33, height=5.53, dpi=300)
}

# Before the reshape, add a new set of columns (53 columns) coding whether a 
# new marriage occurred prior to the survey in the month. Do this by using the 
# marit columns.
# 	First: recode 1 and 2 (married living with/without spouse) as 2, meaning 
# 	married in that month. Recode 3, 4, and 5 (unmarried, widowed, and 
# 	divorced) as 1, meaning unmarried. Recode 6 (separated, as 4).
#
# 	Next, Subtract the marit1-53 columns from the marit2-54 columns. Now, in 
# 	these new columns:
# 		1 = got married
# 		0 = no change in marital status
# 		-1 = marriage ended
# 		Other numbers have to do with separated -> other status. This is 
# 		ignored for now.
maritcolumns <- grep('^marit[0-9]*$', names(hhreg))
maritstatus <- hhreg[maritcolumns]
maritstatus[maritstatus==-4] <- NA
maritstatus[maritstatus==-3] <- NA
maritstatus[maritstatus==-1] <- NA
maritstatus[maritstatus==1] <- 2
maritstatus[maritstatus==3] <- 1
maritstatus[maritstatus==4] <- 1
maritstatus[maritstatus==5] <- 1
maritstatus[maritstatus==6] <- 4
maritstatus.chg <- maritstatus[2:54] - maritstatus[1:53]
# Add a column for time 1, which is only NAs as marital status is not known 
# prior to the first month, so no change can be calculated.
maritstatus.chg <- cbind(marit1=matrix(NA, nrow(maritstatus.chg),1), maritstatus.chg)
# Rename the columns to maritchg so they do not interfere with the 'marit' 
# column
names(maritstatus.chg) <- sub('^marit', 'maritchg', names(maritstatus.chg))
names(maritstatus) <- sub('^marit', 'maritstat', names(maritstatus))

hhreg <- cbind(hhreg, maritstatus.chg)
hhreg <- cbind(hhreg, maritstatus)

###############################################################################
# First birth timing
###############################################################################
# Pull out all rows where there was a marriage, and where the person is female.  
# These rows are indicated by 
gotmarried <- (maritstatus.chg==1) & (hhreg$gender=="female")
# Find the index of the first marriage in each row.
marriage.month <- apply(gotmarried, 1, function(x) match(1, x))

# Now find the index of the first birth of each row (only in the rows where 
# there was a marriage)
preg.cols <- grep('^preg[0-9]*$', names(hhreg))
births <- hhreg[preg.cols]
births <- births==3 | births==5
firstbirth.month <- apply(births, 1, function(x) match(TRUE, x))

gotmarried.rows <- marriage.month > 0
gotmarried.rows[is.na(gotmarried.rows)] <- FALSE
firstbirth.times <- firstbirth.month[gotmarried.rows] - marriage.month[gotmarried.rows]
firstbirth.times <- firstbirth.times[!(firstbirth.times<0)]

firstbirthlims <- c(0, 2, 8, 10, 12, 17, 22, 30, 40, 50)
firstbirth.count <- c()
for (limindex in 1:(length(firstbirthlims)-1)) {
    firstbirth.count <- c(firstbirth.count,
            sum(firstbirth.times >= firstbirthlims[limindex] &
            firstbirth.times < firstbirthlims[limindex+1], na.rm=TRUE))
}
firstbirthprob <- data.frame(bin=firstbirthlims[1:(length(firstbirthlims)-1)],
        prob=firstbirth.count)
firstbirthprob$prob <- firstbirthprob$prob/sum(firstbirthprob$prob)

# Also before the reshape, add a new set of columns coding whether an 
# individual is at risk of giving birth. Only females are at risk of giving 
# birth, and they are not at risk of giving birth for the 9 months before and 
# the 9 months after they give birth. A birth is coded as a 3 (livebirth) or a 
# 5 (stillbirth).  The atrisk.birth variable does NOT account for age 
# limitations on births.  This is taken care of by the data itself.
riskbirth <- hhreg[preg.cols]
riskbirth[riskbirth != 3] <- 1
riskbirth[riskbirth == 3 | riskbirth == 5] <- 0
# Now the month in which a woman gave birth is coded as a 0. Also code as 0 the 
# 9 months before and the 9 months after she gave birth.
atrisk.birth <- riskbirth
for (n in 2:9) {
    # First do 9 months after birth
    cols.mask.forward = n:ncol(atrisk.birth)
    cols.multiplier.forward = 1:(ncol(atrisk.birth) - n +1)
    atrisk.birth[cols.mask.forward] <- atrisk.birth[cols.mask.forward] *
            riskbirth[cols.multiplier.forward]
    # Now do 9 months prior to birth
    cols.mask.back = 1:(ncol(atrisk.birth)-n+1)
    cols.multiplier.back = n:ncol(atrisk.birth)
    atrisk.birth[cols.mask.back] <- atrisk.birth[cols.mask.back] *
            riskbirth[cols.multiplier.back]

}
# Code the first 9 months as zeros as we don't know if a woman gave birth or 
# not (missing the first 9 months of data).
atrisk.birth[1:9] <- 0
atrisk.birth[hhreg$gender != "female",] <- 0
names(atrisk.birth) <- sub('^preg', 'atrisk.birth', names(atrisk.birth))
hhreg <- cbind(hhreg, atrisk.birth)

###############################################################################
# Now do the reshape.
###############################################################################
# Find the column indices of all columns that are repeated measurements
columns <- grep('^(livng|age|preg|marit|maritchg|maritstat|place|atrisk.birth)[0-9]*$', names(hhreg))

# Reshape age and livngs. Include columns 1, 3, and 4 as these are respid, 
# ethnic, and gender, respectively.
events <- reshape(hhreg[c(1, 3, 4, columns)], direction="long",
        varying=names(hhreg[columns]), idvar="respid", timevar="time", sep="")

###############################################################################
# Process age/livngs/hasspouse/marr to recode and remove NAs, etc.
###############################################################################
# Add a new column "has spouse" that is 0 if a person is not married, 1 if a 
# person is married. Do they by recoding the MARIT data. Recode unmarried, 
# widowed, divorced and separated (3, 4, 5 and 6) as 0, and married living with 
# spouse and married not living with spouse (1 and 2) to 1.
events <- cbind(events, hasspouse=matrix(NA,nrow(events),1))
events$hasspouse <- events$marit
events$hasspouse[events$hasspouse==2] <- 1
events$hasspouse[events$hasspouse!=1] <- 0

# Here I recode the livng data so any point where an individual was known alive 
# is a 2, the period in which they died is a 3, and all other times (including 
# when they were away (alive/dead unknown) is a 1.
# TODO: Better data could be had be going through and finding people who were 
# away for several months but returned. The months when they were away can be 
# counted as person months in the calculations because, if they returned, it is 
# known that they were alive while they were gone. The current method therefore 
# biases the mortality estimates upwards slightly, by not taking account of 
# months when people who returned to the study were away.
events$livng[events$livng==4] <- 2 # Code new HH member as alive
events$livng[events$livng==5] <- 2 # Code HH merged as alive
events$livng[events$livng==6] <- 1 # Code away from HH as unknown
events$livng[is.na(events$livng)] <- 1 # Code NA as unknown
events$livng[events$livng != 2 & events$livng != 3] <- 1 # Code all others as unknown

# Drop rows where livng is unknown
events <- events[-which(events$livng==1),]

# Drop rows where age is unknown
events <- events[-which(events$age<0),]

# Drop the one individual where ethnicity is missing
events <- events[-which(is.na(events$ethnic)),]

# Drop rows where hasspouse has NAs
events <- events[-which(is.na(events$hasspouse)),]

###############################################################################
# Process deaths.
###############################################################################
# Add a column to store the bin index for each record (determined by the
# person's age).
events <- cbind(events, deathbin=matrix(0,nrow(events),1))

deathlims <- c(0, 3, 6, 12, 20, 40, 60, 80, 90, 199)
# First count number of person months in each bin
for (limindex in 1:(length(deathlims)-1)) {
    events[events$age>=deathlims[limindex] &
            events$age<deathlims[limindex+1],]$deathbin <- deathlims[limindex]
}

# Then count the number of death events per bin
deaths <- aggregate(events$livng==3, by=list(gender=events$gender,
        deathbin=events$deathbin), sum)
deathspsnmnths <- aggregate(events$livng==2, by=list(gender=events$gender,
        deathbin=events$deathbin), sum)
deathprob <- data.frame(gender=deaths$gender, bin=deaths$deathbin,
        prob=(deaths$x/deathspsnmnths$x)*12)
# Set the deathprob for men equal to that for women for the last bin, as the 
# men prob is lower since.
deathprob[17,3] <- deathprob[18,3]

###############################################################################
# Process births.
###############################################################################
# Note that hhreg data is only available for pregnancy/births Note that every 
# live birth is a 3 and all other pregnancy statuses (1, 2, 4, 5, and 6) are 
# ignored. Males are always coded as -1 for preg status. NOTE: This means that 
# events$preg is only meaningful in conjunction with events$livng to make sure 
# that only live people are counted, and with events$gender to ensure only 
# women are counted.

# Preg status is only recorded in the hhreg data for women between the ages of 
# 18 and 45.
events <- cbind(events, pregbin=matrix(0,nrow(events),1))
preglims <- c(0, 15, 16, 18, 20, 23, 26, 30, 35, 40, 45, 199)
for (limindex in 1:(length(preglims)-1)) {
    events[events$age>=preglims[limindex] &
            events$age<preglims[limindex+1],]$pregbin <- preglims[limindex]
}
# Then count the number of births per bin, only considering married women 
# (there are only 2 births to unmarried women)
fecund <- events[events$gender=="female" & !is.na(events$preg),]
births <- with(fecund[fecund$hasspouse==1,], aggregate(preg==3,
        by=list(pregbin=pregbin), sum, na.rm=T))

birthpsnmnths <- aggregate(fecund$atrisk.birth==1,
        by=list(pregbin=fecund$pregbin), sum, na.rm=T)
birthprob <- data.frame(bin=births$pregbin, prob=(births$x/birthpsnmnths$x)*12)

# TODO: Also calculate the proportion of female/male births
###############################################################################
# Process marriages.
###############################################################################
events <- cbind(events, marrbin=matrix(0,nrow(events),1))
marrlims <- c(0, 10, 14, 18, 22, 30, 40, 60, 199)
for (limindex in 1:(length(marrlims)-1)) {
    events[events$age>=marrlims[limindex] &
            events$age<marrlims[limindex+1],]$marrbin <- marrlims[limindex]
}

events$maritchg[is.na(events$maritchg)] <- 0
marriages <- aggregate(events$maritchg==1, by=list(gender=events$gender,
                marrbin=events$marrbin), sum)
# Remove NAs from maritstat
events$maritstat[is.na(events$maritstat)] <- 0
marrpsnmnths <- aggregate(events$maritstat==1, by=list(gender=events$gender,
        marrbin=events$marrbin), sum)
marrprob <- data.frame(gender=marriages$gender, bin=marriages$marrbin,
        prob=(marriages$x/marrpsnmnths$x)*12)
###############################################################################
# Process migrations.
###############################################################################


###############################################################################
# Now write out probabilities to text
###############################################################################
txthazards <- c()
txthazards <- c(txthazards, make.txthazard(birthprob$prob, preglims,
        "hazard.birth"))
txthazards <- c(txthazards, make.txtprob(firstbirthprob$prob,
        c(firstbirthprob$bin, 50), "prob.firstbirth.times"))
txthazards <- c(txthazards,
        make.txthazard(deathprob[deathprob$gender=="male",]$prob,
        deathlims, "hazard.death.male"))
txthazards <- c(txthazards,
        make.txthazard(deathprob[deathprob$gender=="female",]$prob,
        deathlims, "hazard.death.female"))
txthazards <- c(txthazards,
        make.txthazard(marrprob[marrprob$gender=="male",]$prob,
        marrlims, "hazard.marriage.male"))
txthazards <- c(txthazards,
        make.txthazard(marrprob[marrprob$gender=="female",]$prob,
        marrlims, "hazard.marriage.female"))
write(txthazards, file="hazards.txt")

theme_update(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=1))
update_geom_defaults("step", aes(size=1))

qplot(bin, prob*100, geom="step", xlab="Age (years)",
        ylab="Annual Probability of Live Birth (%)",
        data=birthprob)
ggsave("prob_birth.png", width=8.33, height=5.53, dpi=300)

qplot(bin, prob*100, geom="step", colour=gender, xlab="Age (years)",
        ylab="Annual Probability of Dying (%)", data=deathprob)
ggsave("prob_death.png", width=8.33, height=5.53, dpi=300)

qplot(bin, prob*100, geom="step", colour=gender, xlab="Age (years)",
        ylab="Annual Probability of Marrying (%)", data=marrprob)
ggsave("prob_marriage.png", width=8.33, height=5.53, dpi=300)

qplot(bin, prob*100, geom="step", xlab="Time to First Birth (months)",
        ylab="Probability (%)", data=firstbirthprob)
ggsave("prob_first_birth.png", width=8.33, height=5.53, dpi=300)

###############################################################################
# Setup the altered first birth timing scenario.

firstbirth.count.late <- c(9, 42, 126, 262, 313, 140, 70, 33, 5)
firstbirthlims.late <- c(0, 2, 5, 10, 15, 20, 25, 30, 35, 40, 50)
firstbirth.count.late <- c(2, 10, 20, 100, 190, 210, 190, 100, 20, 10)
firstbirthprob.late <- data.frame(bin=firstbirthlims.late[1:(length(firstbirthlims.late)-1)],
        prob=firstbirth.count.late)
firstbirthprob.late$prob <- firstbirthprob.late$prob/sum(firstbirthprob.late$prob)
txthazards.altered <- c(make.txtprob(firstbirthprob.late$prob,
        c(firstbirthprob.late$bin, 50), "prob.firstbirth.times"))
write(txthazards.altered, file="hazards_first_birth_delayed.txt")
qplot(bin, prob*100, geom="step", xlab="Time to First Birth (months)",
        ylab="Probability (%)", data=firstbirthprob.late)
ggsave("prob_first_birth_altered.png", width=8.33, height=5.53, dpi=300)
