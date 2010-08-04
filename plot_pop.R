#!/usr/bin/env Rscript
# Plots the pop data from a model run.
require(ggplot2)

#MODEL_RUN_ID <- commandArgs(trailingOnly=TRUE)[1]
#DATA_PATH <- paste("~/Data/ChitwanABM_runs", MODEL_RUN_ID, sep="/")
DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

theme_update(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=1))

pop.results <- read.csv(paste(DATA_PATH, "pop_results.csv", sep="/"))

# Read in time data to use in plotting. time.Robj will provide the x-axis 
# values.
time.values <- read.csv(paste(DATA_PATH, "time.csv", sep="/"))
time.Robj <- as.Date(paste(time.values$time_date, "15", sep=","),
        format="%m/%Y,%d")
time.values <- cbind(time.values, time.Robj=time.Robj)

num_psn.cols <- grep('^num_psn.[0-9]*$', names(pop.results))
num_hs.cols <- grep('^num_hs.[0-9]*$', names(pop.results))
# num_marr is total number of marriages in the neighborhood, whereas marr is 
# the number of new marriages in a particular month.
num_marr.cols <- grep('^num_marr.[0-9]*$', names(pop.results))
marr.cols <- grep('^marr.[0-9]*$', names(pop.results))
births.cols <- grep('^births.[0-9]*$', names(pop.results))
deaths.cols <- grep('^deaths.[0-9]*$', names(pop.results))
in_migr.cols <- grep('^in_migr.[0-9]*$', names(pop.results))
out_migr.cols <- grep('^out_migr.[0-9]*$', names(pop.results))

# Make two separate stacks - one of pop data, and one of event data.
# Stack them so they can easily be used with ggplot2 faceting.
events <- data.frame(time.Robj=time.Robj,
        marr=apply(pop.results[marr.cols], 2, sum, na.rm=TRUE), 
        births=apply(pop.results[births.cols], 2, sum, na.rm=TRUE), 
        deaths=apply(pop.results[deaths.cols], 2, sum, na.rm=TRUE), 
        in_migr=apply(pop.results[in_migr.cols], 2, sum, na.rm=TRUE), 
        out_migr=apply(pop.results[out_migr.cols], 2, sum, na.rm=TRUE))
events <- stack(events)
events <- cbind(time.Robj=rep(time.Robj,5), events)
names(events)[2:3] <- c("events", "Event_type")

# Plot thinner lines so this busy plot is easier to read.
update_geom_defaults("line", aes(size=.5))
qplot(time.Robj, events, geom="line", colour=Event_type, xlab="Year",
        ylab="Number of Events", data=events)
ggsave(paste(DATA_PATH, "pop_events.png", sep="/"), width=8.33, height=5.53,
        dpi=300)

update_geom_defaults("line", aes(size=1))
num.psn <- data.frame(time.Robj=time.Robj,
        num.psn=apply(pop.results[num_psn.cols], 2, sum, na.rm=TRUE))
qplot(time.Robj, num.psn, geom="line", xlab="Year",
        ylab="Population", data=num.psn)
ggsave(paste(DATA_PATH, "pop_num_psn.png", sep="/"), width=8.33, height=5.53,
        dpi=300)

num.other <- data.frame(time.Robj=time.Robj,
        num.hs=apply(pop.results[num_hs.cols], 2, sum, na.rm=TRUE), 
        num.marr=apply(pop.results[num_marr.cols], 2, sum, na.rm=TRUE))
num.other <- stack(num.other)
num.other <- cbind(time.Robj=rep(time.Robj,2), num.other)
names(num.other)[2:3] <- c("num", "Pop_type")
qplot(time.Robj, num, geom="line", colour=Pop_type, xlab="Year",
        ylab="Population", data=num.other)
ggsave(paste(DATA_PATH, "pop_num_hs_marr.png", sep="/"), width=8.33, height=5.53,
        dpi=300)
