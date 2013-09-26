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
# See the README.txt file for author contact information.

library(ggplot2, quietly=TRUE)
library(reshape)

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53
theme_set(theme_grey(base_size=16))
update_geom_defaults("line", aes(size=1))

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
if (is.na(DATA_PATH)) stop("Data path must be supplied")

calc_event_data <- function(event_type, run_path) {
    events_data <- read.csv(paste(run_path, "person_events.log", sep="/"), na.strings=c("NA", "None"))
    events <- events_data[grep('^(nid|age|time|event|marrtime)$', names(events_data))]
    events <- events[events$event %in% event_type, ]
    return(events)
}

time_values <- read.csv(paste(DATA_PATH, "time.csv", sep="/"))
time.Robj <- as.Date(paste(time_values$time_date, "15", sep=","),
        format="%m/%Y,%d")
time_values <- cbind(time_values, time.Robj=time.Robj)
time_values$year <- floor(time_values$time_float)

first_births <- calc_event_data("First birth", DATA_PATH)
first_births$time <- (first_births$time - 1997)*12
first_births <- merge(first_births, time_values, by.x="time", by.y="timestep")
first_births$fb_int <- (first_births$time_float - first_births$marrtime) * 12
first_births <- cbind(first_births, ones=rep(1, nrow(first_births)))

first_births <- aggregate(first_births$ones, by=list(time=first_births$time.Robj), sum)
qplot(time, x, data=first_births, geom="line", ylab="Number of First Births", xlab="Time")
ggsave(paste(DATA_PATH, "first_births.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

subsequent_births <- calc_event_data("Subsequent birth", DATA_PATH)
subsequent_births <- merge(subsequent_births, time_values, by.x="time", by.y="timestep")
subsequent_births <- cbind(subsequent_births, ones=rep(1, nrow(subsequent_births)))

subsequent_births <- aggregate(subsequent_births$ones, by=list(time=subsequent_births$time.Robj), sum)
qplot(time, x, data=subsequent_births, geom="line", ylab="Number of Subsequent Births", xlab="Time")
ggsave(paste(DATA_PATH, "subsequent_births.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)
