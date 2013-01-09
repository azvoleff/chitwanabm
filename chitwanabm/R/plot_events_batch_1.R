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
if (length(directories) < 1) stop(paste("can't run plot_events_batch with", length(directories), "model runs."))
if (length(directories) < 5) warning(paste("Only", length(directories), "model runs found."))

###############################################################################
time_values <- read.csv(paste(directories[1], "time.csv", sep="/"))
time.Robj <- as.Date(paste(time_values$time_date, "15", sep=","),
        format="%m/%Y,%d")
time_values <- cbind(time_values, time.Robj=time.Robj)
time_values$year <- floor(time_values$time_float)

calc_first_birth_time <- function(event_type, run_path) {
    events_data <- read.csv(paste(run_path, "person_events.log", sep="/"), na.strings=c("NA", "None"))
    events <- events_data[grep('^(nid|age|gender|time|event|marrtime|is_initial_agent|is_in_migrant|pid)$', names(events_data))]
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

    # Merge the land cover type data so results can be plotted by cover class
    results <- read.csv(paste(directory, "run_results.csv", sep="/"))
    nbh.area <- apply(cbind(results$agveg.1, results$nonagveg.1, results$pubbldg.1,
                results$privbldg.1, results$other.1), 1, sum)
    lcdata <- data.frame(nid=results$neighid, pctagveg.initial=(results$agveg.1 / nbh.area) * 100)
    final_agveg_col <- grep(paste('^agveg.', max(time_values$timestep), '$', sep=""), names(results))
    lcdata$pctagveg.final  <- (results[, final_agveg_col] / nbh.area) * 100
    lcdata$pctagveg.change <- lcdata$pctagveg.initial - lcdata$pctagveg.final
    # Also calculate difference in log of percent, since model uses log percent
    lcdata$pctagveg.lninitial <- log(lcdata$pctagveg.initial + 1)
    lcdata$pctagveg.lnfinal <- log(lcdata$pctagveg.final + 1)
    lcdata$pctagveg.lnchange <- lcdata$pctagveg.lninitial - lcdata$pctagveg.lnfinal

    events.new <- merge(events.new, lcdata)

    if (n==1) {events <- events.new}
    else {events <- rbind(events, events.new)}
    n <- n + 1
}

events$lctype <- cut(events$pctagveg.initial, quantile(events$pctagveg.initial), 
                      labels=c('Urban', 'Semi-urban', 'Semi-agricultural', 
                               'Agricultural'))
events$lctype[is.na(events$lctype)] <- levels(events$lctype)[1]
events$lcctype <- cut(events$pctagveg.change, quantile(events$pctagveg.change), 
                      labels=c('1st quartile', '2nd quartile', '3rd quartile', 
                               '4th quartile'))
events$lcctype[is.na(events$lcctype)] <- levels(events$lcctype)[1]

events$lnlcctype <- cut(events$pctagveg.lnchange, quantile(events$pctagveg.lnchange), 
                      labels=c('1st quartile', '2nd quartile', '3rd quartile', 
                               '4th quartile'))
events$lnlcctype[is.na(events$lnlcctype)] <- levels(events$lnlcctype)[1]

###############################################################################
# First analyze first birth intervals:
first_births <- events[events$event == "First birth" & events$is_in_migrant == "False", ]
# Can't accurately calculate first birth time for women at beginning of the 
# model, since their month of marriage is unknown (not included in the CVFS 
# survey).
first_births <- first_births[first_births$time_float >= 1999, ]
mean_fb_int_allruns <- aggregate(first_births$fb_int, by=list(year=first_births$year, 
                                                        runname=first_births$runname, 
                                                        lcctype=first_births$lcctype), 
                                 mean)
names(mean_fb_int_allruns)[grep('^x$', names(mean_fb_int_allruns))] <- 
    'mean_fb_int'

fb_int_means <- aggregate(mean_fb_int_allruns$mean_fb_int, 
                          by=list(year=mean_fb_int_allruns$year, 
                                  lcctype=mean_fb_int_allruns$lcctype), mean)
names(fb_int_means)[grep('^x$', names(fb_int_means))] <- 'fb_int.mean'
fb_int_sds <- aggregate(mean_fb_int_allruns$mean_fb_int, 
                        by=list(year=mean_fb_int_allruns$year, 
                                lcctype=mean_fb_int_allruns$lcctype), sd)
fb_int_means$fb_int.sd <- fb_int_sds$x
fb_int_means$time.Robj <- as.Date(as.character(fb_int_means$year), format="%Y")
write.csv(fb_int_means, file=paste(DATA_PATH, "ens_results_fb_ints.csv", sep="/"), row.names=FALSE)

p <- ggplot()
p + geom_line(aes(time.Robj, fb_int.mean, colour=lcctype), data=fb_int_means) +
    geom_ribbon(aes(x=time.Robj, ymin=(fb_int.mean - 2 * fb_int.sd), 
                    ymax=(fb_int.mean + 2 * fb_int.sd), fill=lcctype),
        alpha=.2, data=fb_int_means) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Time to First Birth (months)', colour="Land-use Change Class")
ggsave(paste(DATA_PATH, "first_birth_intervals.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

# Drop mixed classes:
#fb_int_means_2class <- fb_int_means[!grepl('(Semi-urban|Semi-agricultural)', fb_int_means$lctype), ]
fb_int_means_2class <- fb_int_means[!grepl('(2nd quartile|3rd quartile)', fb_int_means$lcctype), ]
p <- ggplot()
p + geom_line(aes(time.Robj, fb_int.mean, colour=lcctype), data=fb_int_means_2class) +
    geom_ribbon(aes(x=time.Robj, ymin=(fb_int.mean - 2 * fb_int.sd), 
                    ymax=(fb_int.mean + 2 * fb_int.sd), fill=lcctype),
        alpha=.2, data=fb_int_means_2class) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Time to First Birth (months)', colour="Land-use Change Class")
ggsave(paste(DATA_PATH, "first_birth_intervals_2_class.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

###############################################################################
# Now analyze marriage times
marriages <- events[events$event == "Marriage" & events$is_in_migrant == "False", ]
marriages <- marriages[marriages$time_float >= 1999, ]
mean_marr_age_allruns <- aggregate(marriages$age, by=list(year=marriages$year, 
                                                          gender=marriages$gender, 
                                                          runname=marriages$runname, 
                                                          lcctype=marriages$lcctype), 
                                 mean)
names(mean_marr_age_allruns)[grep('^x$', names(mean_marr_age_allruns))] <- 'mean_marr_age'

marr_age_means <- aggregate(mean_marr_age_allruns$mean_marr_age, 
                          by=list(year=mean_marr_age_allruns$year, 
                                  gender=mean_marr_age_allruns$gender, 
                                  lcctype=mean_marr_age_allruns$lcctype), mean)
names(marr_age_means)[grep('^x$', names(marr_age_means))] <- 'marr_age.mean'
marr_age_sds <- aggregate(mean_marr_age_allruns$mean_marr_age, 
                        by=list(year=mean_marr_age_allruns$year, 
                                gender=mean_marr_age_allruns$gender, 
                                lcctype=mean_marr_age_allruns$lcctype), sd)
marr_age_means$marr_age.sd <- marr_age_sds$x
marr_age_means$time.Robj <- as.Date(as.character(marr_age_means$year), format="%Y")

marr_age_means_male <- marr_age_means[marr_age_means$gender == "male", ]
write.csv(marr_age_means_male, file=paste(DATA_PATH, "ens_results_marriage_ages_male.csv", sep="/"), row.names=FALSE)
marr_age_means_female <- marr_age_means[marr_age_means$gender == "female", ]
write.csv(marr_age_means_female, file=paste(DATA_PATH, "ens_results_marriage_ages_female.csv", sep="/"), row.names=FALSE)

p <- ggplot()
p + geom_line(aes(time.Robj, marr_age.mean, colour=lcctype), data=marr_age_means_male) +
    geom_ribbon(aes(x=time.Robj, ymin=(marr_age.mean - 2 * marr_age.sd), 
                    ymax=(marr_age.mean + 2 * marr_age.sd), fill=lcctype),
        alpha=.2, data=marr_age_means_male) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Age (men, years)', colour="Land-use Change Class")
ggsave(paste(DATA_PATH, "marriage_age_men.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

p <- ggplot()
p + geom_line(aes(time.Robj, marr_age.mean, colour=lcctype), data=marr_age_means_female) +
    geom_ribbon(aes(x=time.Robj, ymin=(marr_age.mean - 2 * marr_age.sd), 
                    ymax=(marr_age.mean + 2 * marr_age.sd), fill=lcctype),
        alpha=.2, data=marr_age_means_female) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Age (women, years)', colour="Land-use Change Class")
ggsave(paste(DATA_PATH, "marriage_age_women.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)


# Drop mixed classes:
#marr_age_means_male_2class <- marr_age_means_male[!grepl('(Semi-urban|Semi-agricultural)', marr_age_means_male$lctype), ]
marr_age_means_male_2class <- marr_age_means_male[!grepl('(2nd quartile|3rd quartile)', marr_age_means_male$lcctype), ]
p <- ggplot()
p + geom_line(aes(time.Robj, marr_age.mean, colour=lcctype), data=marr_age_means_male_2class) +
    geom_ribbon(aes(x=time.Robj, ymin=(marr_age.mean - 2 * marr_age.sd), 
                    ymax=(marr_age.mean + 2 * marr_age.sd), fill=lcctype),
        alpha=.2, data=marr_age_means_male_2class) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Age (men, years)', colour="Land-use Change Class")
ggsave(paste(DATA_PATH, "marriage_age_men_2_class.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

#marr_age_means_female_2class <- marr_age_means_female[!grepl('(Semi-urban|Semi-agricultural)', marr_age_means_female$lctype), ]
marr_age_means_female_2class <- marr_age_means_female[!grepl('(2nd quartile|3rd quartile)', marr_age_means_female$lcctype), ]
p <- ggplot()
p + geom_line(aes(time.Robj, marr_age.mean, colour=lcctype), data=marr_age_means_female_2class) +
    geom_ribbon(aes(x=time.Robj, ymin=(marr_age.mean - 2 * marr_age.sd), 
                    ymax=(marr_age.mean + 2 * marr_age.sd), fill=lcctype),
        alpha=.2, data=marr_age_means_female_2class) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Age (women, years)', colour="Land-use Change Class")
ggsave(paste(DATA_PATH, "marriage_age_women_2_class.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)
