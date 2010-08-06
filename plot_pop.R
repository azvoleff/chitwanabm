#!/usr/bin/env Rscript
# Plots the pop data from a model run.
require(ggplot2)

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
#MODEL_RUN_ID <- '20100804-204228'
#DATA_PATH <- paste("~/Data/ChitwanABM_runs", MODEL_RUN_ID, sep="/")

pop.results <- calc_NBH_pop(DATA_PATH)

# Make two separate stacks - one of monthly event data and one of total hs and 
# total marriages. Stack them so they can easily be color-coded with ggplot2.
events <- with(pop.results, data.frame(time.Robj=time.Robj, marr, births, deaths))
events <- stack(events)
events <- cbind(time.Robj=rep(pop.results$time.Robj, 3), events)
names(events)[2:3] <- c("events", "Event_type")

num.hs.marr <- with(pop.results, data.frame(time.Robj=time.Robj, num_hs, num_marr))
num.hs.marr <- stack(num.hs.marr)
num.hs.marr <- cbind(time.Robj=rep(pop.results$time.Robj,2), num.hs.marr)
names(num.hs.marr)[2:3] <- c("num", "Pop_type")

# First plot monthly event data
theme_update(theme_grey(base_size=18))
# Plot thinner lines so this busy plot is easier to read.
update_geom_defaults("line", aes(size=.5))
qplot(pop.results$time.Robj, events, geom="line", colour=Event_type, xlab="Year",
        ylab="Number of Events", data=events)
ggsave(paste(DATA_PATH, "pop_events.png", sep="/"), width=8.33, height=5.53,
        dpi=300)

# Now plot total households and total marriages
qplot(time.Robj, num, geom="line", colour=Pop_type, xlab="Year",
        ylab="Population", data=num.hs.marr)
ggsave(paste(DATA_PATH, "pop_num_hs_marr.png", sep="/"), width=8.33, height=5.53,
        dpi=300)

# Plot total population
update_geom_defaults("line", aes(size=1))
qplot(time.Robj, num_psn, geom="line", xlab="Year",
        ylab="Population", data=pop.results)
ggsave(paste(DATA_PATH, "pop_num_psn.png", sep="/"), width=8.33, height=5.53,
        dpi=300)

# Plot fw consumption in metric tons
qplot(time.Robj, fw_usage_kg/1000, geom="line", xlab="Year",
        ylab="Metric Tons of Fuelwood", data=pop.results)
ggsave(paste(DATA_PATH, "fw_usage.png", sep="/"), width=8.33, height=5.53,
        dpi=300)
