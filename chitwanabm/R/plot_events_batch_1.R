#!/usr/bin/env Rscript
#
# Copyright 2008-2012 Alex Zvoleff
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

library(ggplot2, quietly=TRUE)
library(reshape)

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53
theme_set(theme_grey(base_size=16))
update_geom_defaults("line", aes(size=1))

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

directories <- list.dirs(DATA_PATH, recursive=FALSE)
# Only match the model results folders - don't match any other folders or files 
# in the directory, as trying to read results from these other files/folders 
# would lead to an error.
directories <- directories[grep("[0-9]{8}-[0-9]{6}", directories)]
if (length(directories)<1) stop(paste("can't run plot_events_batch with", length(directories), "model runs."))
if (length(directories)<5) warning(paste("Only", length(directories), "model runs found."))

time_values <- read.csv(paste(directories[1], "time.csv", sep="/"))
time.Robj <- as.Date(paste(time_values$time_date, "15", sep=","),
        format="%m/%Y,%d")
time_values <- cbind(time_values, time.Robj=time.Robj)
time_values$year <- floor(time_values$time_float)

calc_first_birth_time <- function(event_type, run_path) {
    events_data <- read.csv(paste(run_path, "person_events.log", sep="/"), na.strings=c("NA", "None"))
    events <- events_data[grep('^(nid|age|time|event|marrtime)$', names(events_data))]
    events <- merge(events, time_values, by.x="time", by.y="timestep")
    events <- events[events$event %in% event_type, ]
    events$fb_int <- round((events$time_float - events$marrtime) * 12, digits=0) 
    return(events)
}

event_type <- c("First birth", "Marriage")
n <- 1
for (directory in directories) {
    possible_error <- tryCatch(events.new <- calc_first_birth_time(event_type, directory), 
                               error=function(e) e)
    # Catch cases where results file does not exist (because run was 
    # interrupted, run is not yet finished, etc.)
    if (inherits(possible_error, "error")) {
        warning(paste("Error reading", directory))
        next
    }
    runname <- paste("run", n, sep="")
    events.new <- cbind(events.new, runname=rep(runname, nrow(events.new)))
    if (n==1) {events <- events.new}
    else {events <- rbind(events, events.new)}
    n <- n + 1
}

# Merge the initial cover types so results can be plotted by cover class
results <- read.csv(paste(directories[1], "run_results.csv", sep="/"))
nbh.area <- apply(cbind(results$agveg.1, results$nonagveg.1, results$pubbldg.1,
            results$privbldg.1, results$other.1), 1, sum)
results$pctagveg.1 <- (results$agveg.1 / nbh.area) * 100
#results$lctype <- cut(results$pctagveg.1, c(-.01, 25, 50, 75, 100), 
#                      labels=c('Urban', 'Mixed Urban', 'Mixed Agriculture', 
#                      'Agriculture'))
results$lctype <- cut(results$pctagveg.1, quantile(results$pctagveg.1), 
                      labels=c('Urban', 'Semi-urban', 'Semi-agricultural', 
                               'Agricultural'))
cover_types <- data.frame(neighid=results$neighid, lctype=results$lctype)
events <- merge(events, cover_types, by.x="nid", by.y="neighid")

# First analyze first birth intervals:
first_births <- events[events$event == "First birth", ]
# Can't accurately calculate first birth time for women at beginning of the 
# model, since their month of marriage is unknown (not included in the CVFS 
# survey).
first_births <- first_births[first_births$time_float >= 1999, ]
mean_fb_int_allruns <- aggregate(first_births$fb_int, by=list(year=first_births$year, 
                                                        runname=first_births$runname, 
                                                        lctype=first_births$lctype), 
                                 mean)
names(mean_fb_int_allruns)[grep('^x$', names(mean_fb_int_allruns))] <- 
    'mean_fb_int'

fb_int_means <- aggregate(mean_fb_int_allruns$mean_fb_int, 
                          by=list(year=mean_fb_int_allruns$year, 
                                  lctype=mean_fb_int_allruns$lctype), mean)
names(fb_int_means)[grep('^x$', names(fb_int_means))] <- 'fb_int.mean'
fb_int_sds <- aggregate(mean_fb_int_allruns$mean_fb_int, 
                        by=list(year=mean_fb_int_allruns$year, 
                                lctype=mean_fb_int_allruns$lctype), sd)
fb_int_means$fb_int.sd <- fb_int_sds$x
fb_int_means$year <- as.Date(as.character(fb_int_means$year), format="%Y")
write.csv(fb_int_means, file=paste(DATA_PATH, "ens_results_marriage_fb_ints.csv", sep="/"), row.names=FALSE)

p <- ggplot()
p + geom_line(aes(year, fb_int.mean, colour=lctype), data=fb_int_means) +
    geom_ribbon(aes(x=year, ymin=(fb_int.mean - 2 * fb_int.sd), 
                    ymax=(fb_int.mean + 2 * fb_int.sd), fill=lctype),
        alpha=.2, data=fb_int_means) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Time to First Birth (months)', colour="Cover Class")
ggsave(paste(DATA_PATH, "first_birth_intervals.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

# Drop mixed classes:
fb_int_means_2class <- fb_int_means[!grepl('(Semi-urban|Semi-agricultural)', fb_int_means$lctype), ]
p <- ggplot()
p + geom_line(aes(year, fb_int.mean, colour=lctype), data=fb_int_means_2class) +
    geom_ribbon(aes(x=year, ymin=(fb_int.mean - 2 * fb_int.sd), 
                    ymax=(fb_int.mean + 2 * fb_int.sd), fill=lctype),
        alpha=.2, data=fb_int_means_2class) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Time to First Birth (months)', colour="Cover Class")
ggsave(paste(DATA_PATH, "first_birth_intervals_2_class.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

# Now analyze marriage times
marriages <- events[events$event == "Marriage", ]
marriages <- marriages[marriages$time_float >= 1999, ]
mean_marr_age_allruns <- aggregate(marriages$age, by=list(year=marriages$year, 
                                                        runname=marriages$runname, 
                                                        lctype=marriages$lctype), 
                                 mean)
names(mean_marr_age_allruns)[grep('^x$', names(mean_marr_age_allruns))] <- 
    'mean_marr_age'

marr_age_means <- aggregate(mean_marr_age_allruns$mean_marr_age, 
                          by=list(year=mean_marr_age_allruns$year, 
                                  lctype=mean_marr_age_allruns$lctype), mean)
names(marr_age_means)[grep('^x$', names(marr_age_means))] <- 'marr_age.mean'
marr_age_sds <- aggregate(mean_marr_age_allruns$mean_marr_age, 
                        by=list(year=mean_marr_age_allruns$year, 
                                lctype=mean_marr_age_allruns$lctype), sd)
marr_age_means$marr_age.sd <- marr_age_sds$x
marr_age_means$year <- as.Date(as.character(marr_age_means$year), format="%Y")
write.csv(marr_age_means, file=paste(DATA_PATH, "ens_results_marriage_ages.csv", sep="/"), row.names=FALSE)

p <- ggplot()
p + geom_line(aes(year, marr_age.mean, colour=lctype), data=marr_age_means) +
    geom_ribbon(aes(x=year, ymin=(marr_age.mean - 2 * marr_age.sd), 
                    ymax=(marr_age.mean + 2 * marr_age.sd), fill=lctype),
        alpha=.2, data=marr_age_means) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Age (years)', colour="Cover Class")
ggsave(paste(DATA_PATH, "marriage_age.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

# Drop mixed classes:
marr_age_means_2class <- marr_age_means[!grepl('(Semi-urban|Semi-agricultural)', marr_age_means$lctype), ]
p <- ggplot()
p + geom_line(aes(year, marr_age.mean, colour=lctype), data=marr_age_means_2class) +
    geom_ribbon(aes(x=year, ymin=(marr_age.mean - 2 * marr_age.sd), 
                    ymax=(marr_age.mean + 2 * marr_age.sd), fill=lctype),
        alpha=.2, data=marr_age_means_2class) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Age (years)', colour="Cover Class")
ggsave(paste(DATA_PATH, "marriage_age_2_class.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)


