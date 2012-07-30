#!/usr/bin/env Rscript
#
# Copyright 2008-2012 Alex Zvoleff
#
# This file is part of the ChitwanABM agent-based model.
# 
# ChitwanABM is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# ChitwanABM is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# ChitwanABM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff in the Department of Geography at San Diego State 
# University with any comments or questions. See the README.txt file for 
# contact information.

###############################################################################
# Plots the aggregate pop data from a model run (births, deaths, marriages, 
# migration, total population, etc.).
###############################################################################

library(reshape)
library(ggplot2, quietly=TRUE)
library(scales, quietly=TRUE) # Used for formatting time on the x axis

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

pop.results <- calc_NBH_pop(DATA_PATH)

# Make several separate stacks - one of monthly vital event data, one of 
# monthly migration data, and one of total hs and total marriages. Stack them 
# so they can easily be color-coded with ggplot2.
vital_events <- with(pop.results, data.frame(time.Robj=time.Robj, marr, births, deaths))
vital_events <- melt(vital_events, id.vars="time.Robj")
names(vital_events)[2:3] <- c("Event_type", "events")

migrations <- with(pop.results, data.frame(time.Robj=time.Robj, in_migr, out_migr))
migrations <- melt(migrations, id.vars="time.Robj")
names(migrations)[2:3] <- c("Event_type", "events")

num.hs.marr <- with(pop.results, data.frame(time.Robj=time.Robj, num_hs, num_marr))
num.hs.marr <- melt(num.hs.marr, id.vars="time.Robj")
names(num.hs.marr)[2:3] <- c("Pop_type", "num")

# First plot monthly event data
theme_update(theme_grey(base_size=18))
# Plot thinner lines so this busy plot is easier to read.
update_geom_defaults("line", aes(size=.75))
# Plot vital events
p <- qplot(time.Robj, events, geom="line", linetype=Event_type, 
           xlab="Year", ylab="Number of Events", data=vital_events)
p + scale_linetype_discrete(name="Legend",
                            breaks=c("births", "deaths", "marr"),
                            labels=c("Births", "Deaths",
                                     "Marriages"))
ggsave(paste(DATA_PATH, "pop_events.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT,
        dpi=300)

# Plot migration
p <- qplot(time.Robj, events, geom="line", linetype=Event_type, 
           xlab="Year", ylab="Number of Migrants", data=migrations)
p + scale_linetype_discrete(name="Legend",
                            breaks=c("in_migr", "out_migr"),
                            labels=c("In-migrants", "Out-migrants"))
ggsave(paste(DATA_PATH, "migrations.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT,
        dpi=300)

# Now plot total households and total marriages
p <- ggplot(aes(x=time.Robj, y=num), data=num.hs.marr)
p + geom_line(aes(linetype=Pop_type)) +
    labs(x="Year", y="Population") + 
    scale_linetype_discrete(name="Legend",
                            breaks=c("num_hs", "num_marr"),
                            labels=c("Total Households",
                                     "Total Marriages"))
ggsave(paste(DATA_PATH, "pop_num_hs_marr.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)

# Plot total population
p <- qplot(time.Robj, num_psn, geom="line", xlab="Year",
        ylab="Population", data=pop.results)
ggsave(paste(DATA_PATH, "pop_num_psn.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)

# Plot fw consumption in metric tons
p <- qplot(time.Robj, fw_usage_kg/1000, geom="line", xlab="Year",
        ylab="Metric Tons of Fuelwood", data=pop.results)
ggsave(paste(DATA_PATH, "fw_usage.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)
