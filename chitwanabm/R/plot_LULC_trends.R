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
# See the README.rst file for author contact information.

###############################################################################
# Plots basic LULC data from a model run.
###############################################################################

library(ggplot2, quietly=TRUE)
library(reshape)
library(grid) # for 'unit' function
library(RColorBrewer)

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53

DATA_PATH <- 'R:/Data/Nepal/chitwanabm_runs/Testing_500EVIslope/20130609-154403_azvoleff-think'

initial.options <- commandArgs(trailingOnly = FALSE)
file.arg.name <- "--file="
script.name <- sub(file.arg.name, "", initial.options[grep(file.arg.name, initial.options)])
script.basename <- dirname(script.name)
source(paste(script.basename, "calc_NBH_stats.R", sep="/"))

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
if (is.na(DATA_PATH)) stop("Data path must be supplied")

lulc.sd.mean <- calc_agg_LULC(DATA_PATH)
lulc.sd.mean <- melt(lulc.sd.mean, id.vars="time.Robj")
names(lulc.sd.mean)[2:3] <- c("LULC_type", "area")

# Now actually make the plots
theme_set(theme_grey(base_size=16))
update_geom_defaults("line", aes(size=1))

p <- qplot(time.Robj, area, geom="line", colour=LULC_type, linetype=LULC_type, 
           xlab="Year", ylab="Mean Percentage of Neighborhood", 
           data=lulc.sd.mean)
p + scale_linetype_discrete(name="Land-use Type",
                            breaks=c("agveg", "nonagveg", "pubbldg", 
                                     "privbldg", "other"),
                            labels=c("Agricultural", "Non-agricultural",
                                     "Public Bldgs.", "Private Bldgs.", 
                                     "Other")) +
    scale_colour_discrete(name="Land-use Type",
                            breaks=c("agveg", "nonagveg", "pubbldg", 
                                     "privbldg", "other"),
                            labels=c("Agricultural", "Non-agricultural",
                                     "Public Bldgs.", "Private Bldgs.", 
                                     "Other")) +
    theme(legend.key.width=unit(1, "cm"))

ggsave(paste(DATA_PATH, "LULC.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)

###############################################################################
# Plot EVI trends
run_results <- read.csv(paste(DATA_PATH, "/run_results.csv", sep=""))
EVI <- data.frame(neighid=run_results$neighid,
                  run_results[grep('^EVI.[0-9]*$', names(run_results))])
EVI <- melt(EVI, id.vars='neighid')
EVI$neighid <- factor(EVI$neighid)
# Retrieve the timestep from the variable name string
EVI$timestep <- as.numeric(substr(EVI$variable, 5, 99))
# Drop all except for the January timesteps, since indicator is constant 
# throughout the year.
EVI <- EVI[EVI$timestep %% 12 == 1, ]
EVI$Year <- (EVI$timestep-1)/12 + 1997
EVI_mean <- ddply(EVI, .(Year), summarize,
                  EVI_mean=mean(value))

ggplot() + geom_line(data=EVI, aes(Year, value, colour=neighid), size=.25, show_guide=FALSE) +
    xlab('Year') + ylab('Seasonal Growth (EVI*10,000)') +
    geom_line(data=EVI_mean, aes(Year, EVI_mean), size=1, show_guide=FALSE)
ggsave(paste(DATA_PATH, "EVI_spaghetti.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

###############################################################################
# Plot the transition matrix
lulc_cols <- grep('^(agveg|nonagveg|privbldg|pubbldg|other).[0-9]*$', names(run_results))
lulc_results <- cbind(run_results[lulc_cols])
total_nbh_area <- with(lulc_results, agveg.1 + nonagveg.1 + privbldg.1 + pubbldg.1 + other.1)
max_timestep <- (ncol(lulc_results) / 5) - 1
lulc_results <- (lulc_results / total_nbh_area) * 100
lulc_results <- cbind(neighid=run_results$neighid, lulc_results)

# Cut the initial and final LULC into categories
agveg_class.Initial <- cut(lulc_results$agveg.1, seq(0,100, 25), right=FALSE)
last_agveg_col <- grep(paste('^agveg.', max_timestep, '$', sep=""), names(lulc_results))
agveg_class.Final <- cut(lulc_results[, last_agveg_col], seq(0, 100, 25), right=FALSE)

privbldg_class.Initial <- cut(lulc_results$privbldg.1, seq(0,100, 25), right=FALSE)
last_privbldg_col <- grep(paste('^privbldg.', max_timestep, '$', sep=""), names(lulc_results))
privbldg_class.Final <- cut(lulc_results[, last_privbldg_col], seq(0,100, 25), right=FALSE)

transitions <- data.frame(neighid=lulc_results$neighid, agveg_class.Initial, 
                          agveg_class.Final, privbldg_class.Initial, privbldg_class.Final)
transitions <- reshape(transitions, idvar="neighid", direction="long", 
                       varying=c(2:ncol(transitions)))
transitions <- melt(transitions, id.vars=c("neighid", "time"))
transitions$time <- factor(transitions$time)
transitions$time <- relevel(transitions$time, "Initial")
names(transitions)[names(transitions) == "variable"] <- "lulc_type"
names(transitions)[names(transitions) == "value"] <- "lulc_cut_cat"
forest_distances <- with(run_results, data.frame(neighid, for_dist_BZ_km.1,
                                             for_dist_CNP_km.1,
                                             for_closest_km.1, 
                                             for_closest_type.1))
transitions <- merge(transitions, forest_distances)
transitions$forest_closest_km_cat <- cut(transitions$for_closest_km.1, c(0, 2, 4, 8, 15))

# Set a color blind compatible palette
cbPalette <- c("#999999", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")

p <- qplot(lulc_type, geom="histogram", 
    facets=lulc_cut_cat~time, fill=time,
    data=transitions[transitions$lulc_type=="agveg_class", ], 
    ylab="Number of Neighborhoods", xlab="Agricultural Land-use Category")
p + scale_fill_manual(name="Time", breaks=c("Initial", "Final"), 
                      labels=c("Initial", "Final"), values=cbPalette) + 
    scale_x_discrete(labels=NULL)
ggsave(paste(DATA_PATH, "LULC_transition_agveg.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

p <- qplot(lulc_type, geom="histogram", 
    facets=lulc_cut_cat~time, fill=time,
    data=transitions[transitions$lulc_type=="privbldg_class", ], 
    ylab="Number of Neighborhoods", xlab="Private Buildings Land-use Category")
p + scale_fill_manual(name="Time", breaks=c("Initial", "Final"), 
                      labels=c("Initial", "Final"), values=cbPalette) + 
    scale_x_discrete(labels=NULL)
ggsave(paste(DATA_PATH, "LULC_transition_privbldg.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

# Now make plots faceted by distance to park:
p <- qplot(lulc_type, geom="histogram", 
    facets=lulc_cut_cat~time, fill=forest_closest_km_cat,
    data=transitions[transitions$lulc_type=="agveg_class", ], 
    ylab="Number of Neighborhoods", xlab="Agricultural Land-use Category")
p + scale_fill_manual(name="Forest distance", breaks=c("(0,2]", "(2,4]", 
                                                            "(4,8]", "(8,15]"),
                   labels=c("0-2 km ", "2-4 km ", "4-8 km", "8-12 km"),
                   values=rev(brewer.pal(4, "Greens"))) +
    scale_x_discrete(labels=NULL)
ggsave(paste(DATA_PATH, "LULC_transition_agveg_forest.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

p <- qplot(lulc_type, geom="histogram", 
    facets=lulc_cut_cat~time, fill=forest_closest_km_cat,
    data=transitions[transitions$lulc_type=="privbldg_class", ], 
    ylab="Number of Neighborhoods", xlab="Private Buildings Land-use Category")
p + scale_fill_manual(name="Forest distance", breaks=c("(0,2]", "(2,4]", 
                                                            "(4,8]", "(8,15]"),
                   labels=c("0-2 km ", "2-4 km ", "4-8 km", "8-12 km"),
                   values=rev(brewer.pal(4, "Greens"))) +
    scale_x_discrete(labels=NULL)
ggsave(paste(DATA_PATH, "LULC_transition_privbldg_forest.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)
