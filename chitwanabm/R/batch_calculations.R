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

###############################################################################
# Initialize variables and packages
###############################################################################
library(lubridate)

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

directories <- list.dirs(DATA_PATH, recursive=FALSE)

###############################################################################
# Helper Functions
###############################################################################

calc_event_count <- function(event_type, events_data, results) {
    events <- events_data[grep('^(nid|time|event)$', names(events_data))]
    events <- events[events$event == event_type, ]
    events <- merge(events, time_values, by.x="time", by.y="timestep")
    events <- cbind(events, ones=rep(1, nrow(events)))
    event_count <- aggregate(events$ones, by=list(neighid=events$nid, year=events$year), sum)
    names(event_count)[grep('^x$', names(event_count))] <- 'num_events'
    # If event_type is Marriage, there is one row per new spouse, so the number 
    # of events needs to be halved to get the number of new marriages.
    if (event_type == "Marriage") event_count$num_events <- event_count$num_events / 2
    event_count$year <- year(event_count$year)

    # Normalize events by population of village during that year (using the 
    # population in the first month of the year the events occurred).
    num_psn_cols <- grep('^num_psn.', names(results))
    neigh_pop_cols <- grep('^(neighid|num_psn.)', names(results))
    neigh_pop <- reshape(results[neigh_pop_cols], direction="long", 
                            idvar="neighid", varying=c(2:ncol(results[neigh_pop_cols])))
    neigh_pop$year <- floor(1997 + (neigh_pop$time - 1) / 12)

    nbh_pop <- neigh_pop$num_psn[match(paste(event_count$neighid, 
                                             event_count$year), 
                                       paste(neigh_pop$neighid, 
                                             neigh_pop$year))]

    event_count$num_events_crude_rate <- (event_count$num_events / nbh_pop) * 1000
    return(event_count)
}

calc_first_birth_time <- function(event_type, events_data) {
    events <- events_data[grep('^(nid|age|gender|time|event|marrtime|is_initial_agent|is_in_migrant|pid)$', names(events_data))]
    events <- merge(events, time_values, by.x="time", by.y="timestep")
    events <- events[events$event %in% event_type, ]
    events$fb_int <- round((events$time_float - events$marrtime) * 12, digits=0) 
    return(events)
}

calc_agg_LULC <- function(results, time_values) {
    # Calculate the total land area of each neighborhood
    nbh_area <- apply(cbind(results$agveg.1, results$nonagveg.1, results$pubbldg.1,
            results$privbldg.1, results$other.1), 1, sum)

    # And convert the LULC measurements from units of square meters to units 
    # that are a percentage of total neighborhood area.
    lulc_cols <- grep('^(agveg|nonagveg|pubbldg|privbldg|other).[0-9]*$', 
                      names(results))
    lulc_pct <- results[lulc_cols] / nbh_area

    agveg.cols <- grep('^agveg.[0-9]*$', names(lulc_pct))
    nonagveg.cols <- grep('^nonagveg.[0-9]*$', names(lulc_pct))
    pubbldg.cols <- grep('^pubbldg.[0-9]*$', names(lulc_pct))
    privbldg.cols <- grep('^privbldg.[0-9]*$', names(lulc_pct))
    other.cols <- grep('^other.[0-9]*$', names(lulc_pct))

    lulc_pct.mean <- data.frame(time.Robj=time_values$time.Robj,
            agveg=apply(lulc_pct[agveg.cols], 2, mean),
            nonagveg=apply(lulc_pct[nonagveg.cols], 2, mean),
            pubbldg=apply(lulc_pct[pubbldg.cols], 2, mean),
            privbldg=apply(lulc_pct[privbldg.cols], 2, mean),
            other=apply(lulc_pct[other.cols], 2, mean), row.names=NULL)

    return(lulc_pct.mean)
}

calc_rate_change_agveg <- function(DATA_PATH) {
    # Make plots of LULC for a model run.
    results <- read.csv(paste(DATA_PATH, "run_results.csv", sep="/"),
            na.strings=c("NA", "nan"))

    agveg.cols <- grep('^agveg.[0-9]*$', names(results))
    nonagveg.cols <- grep('^nonagveg.[0-9]*$', names(results))
    pubbldg.cols <- grep('^pubbldg.[0-9]*$', names(results))
    privbldg.cols <- grep('^privbldg.[0-9]*$', names(results))
    other.cols <- grep('^other.[0-9]*$', names(results))

    # Calculate the total land area of each neighborhood
    lulc <- data.frame(nid=results$neighid, 
                       nbh_area=apply(cbind(results$agveg.1, 
                                            results$nonagveg.1, 
                                            results$pubbldg.1,
                                            results$privbldg.1,
                                            results$other.1), 1, sum),
                       results[agveg.cols[3:length(agveg.cols)]])
    # Note that agveg.0 is not included, since it is not defined (it is 0 for 
    # all the neighborhoods).
    agveg_change <- results[agveg.cols[3:length(agveg.cols)]] - results[agveg.cols[2:(length(agveg.cols) - 1)]]
    names(agveg_change) <- gsub('agveg', 'agveg_change', names(agveg_change))
    lulc <- cbind(lulc, agveg_change)
    agveg_vars <- names(lulc)[grep('^agveg.[0-9]*$', names(lulc))]
    agveg_change_vars <- names(lulc)[grep('^agveg_change.[0-9]*$', names(lulc))]

    lulc <- reshape(lulc, idvar="nid", v.names=c("agveg", "agveg_change"),
                    varying=list(agveg_vars, agveg_change_vars),
                    direction="long")

    time_values <- read.csv(paste(DATA_PATH, "time.csv", sep="/"))
    time.Robj <- as.Date(paste(time_values$time_date, "15", sep=","),
            format="%m/%Y,%d")
    time_values <- cbind(time_values, time.Robj=time.Robj)

    lulc$time.Robj <- time_values$time.Robj[match(lulc$time, time_values$timestep)]

    return(lulc)
}

calc_NBH_pop <- function(results, time_values) {
    num_psn.cols <- grep('^num_psn.[0-9]*$', names(results))
    num_hs.cols <- grep('^num_hs.[0-9]*$', names(results))
    # num_marr is total number of marriages in the neighborhood, whereas marr is 
    # the number of new marriages in a particular month.
    num_marr.cols <- grep('^num_marr.[0-9]*$', names(results))
    marr.cols <- grep('^marr.[0-9]*$', names(results))
    births.cols <- grep('^births.[0-9]*$', names(results))
    deaths.cols <- grep('^deaths.[0-9]*$', names(results))
    out_migr_indiv.cols <- grep('^out_migr_indiv.[0-9]*$', names(results))
    ret_migr_indiv.cols <- grep('^ret_migr_indiv.[0-9]*$', names(results))
    in_migr_HH.cols <- grep('^in_migr_HH.[0-9]*$', names(results))
    out_migr_HH.cols <- grep('^out_migr_HH.[0-9]*$', names(results))
    fw_usage.cols <- grep('^fw_usage.[0-9]*$', names(results))

    pop_results <- data.frame(time.Robj=time_values$time.Robj,
            marr=apply(results[marr.cols], 2, sum), 
            births=apply(results[births.cols], 2, sum), 
            deaths=apply(results[deaths.cols], 2, sum),
            out_migr_indiv=apply(results[out_migr_indiv.cols], 2, sum),
            ret_migr_indiv=apply(results[ret_migr_indiv.cols], 2, sum), 
            in_migr_HH=apply(results[in_migr_HH.cols], 2, sum), 
            out_migr_HH=apply(results[out_migr_HH.cols], 2, sum),
            num_hs=apply(results[num_hs.cols], 2, sum), 
            num_marr=apply(results[num_marr.cols], 2, sum),
            num_psn=apply(results[num_psn.cols], 2, sum),
            fw_usage_kg=apply(results[fw_usage.cols], 2, sum))

    return(pop_results)
}

###############################################################################
# Main loop
###############################################################################

n <- 1
pb <- txtProgressBar(min=n, max=length(directories), style=3)
for (directory in directories) {
    setTxtProgressBar(pb, n)
    
    if (!file.exists(paste(directory, "RUN_FINISHED_OK", sep="/"))) {
        warning(paste(directory, "does not contain a finished model run"))
        next
    }

    runname <- paste("run", n, sep="")

    ###########################################################################
    # First load data
    events_data <- read.csv(paste(directory, "person_events.log", sep="/"), na.strings=c("NA", "None"))
    results <- read.csv(paste(directory, "run_results.csv", sep="/"))

    time_values <- read.csv(paste(directory, "time.csv", sep="/"))
    time.Robj <- as.Date(paste(time_values$time_date, "15", sep=","),
            format="%m/%Y,%d")
    time_values <- cbind(time_values, time.Robj=time.Robj)
    time_values$year <- as.Date(cut(time_values$time.Robj, "year"))

    ###########################################################################
    # Make land cover type key, by neighborhood, for later use
    nbh_area <- apply(cbind(results$agveg.1, results$nonagveg.1, results$pubbldg.1,
                results$privbldg.1, results$other.1), 1, sum)
    lcdata <- data.frame(nid=results$neighid, pctagveg.initial=(results$agveg.1 / nbh_area) * 100)
    final_agveg_col <- grep(paste('^agveg.', max(time_values$timestep), '$', sep=""), names(results))
    lcdata$pctagveg.final  <- (results[, final_agveg_col] / nbh_area) * 100
    lcdata$pctagveg.change <- lcdata$pctagveg.initial - lcdata$pctagveg.final
    # Also calculate difference in log of percent, since model uses log percent
    lcdata$pctagveg.lninitial <- log(lcdata$pctagveg.initial + 1)
    lcdata$pctagveg.lnfinal <- log(lcdata$pctagveg.final + 1)
    lcdata$pctagveg.lnchange <- lcdata$pctagveg.lninitial - lcdata$pctagveg.lnfinal

    ###########################################################################
    # Handle calculation of marriage rates
    marriage_events.new <- calc_event_count("Marriage", events_data, results)
    runname <- paste("run", n, sep="")
    num_events_cols <- grep('num_events', names(marriage_events.new))
    names(marriage_events.new)[num_events_cols] <- paste(names(marriage_events.new[num_events_cols]), runname, sep=".")
    if (n==1) {marriage_events <- marriage_events.new}
    else {marriage_events <- merge(marriage_events, marriage_events.new, all=TRUE)}

    ###########################################################################
    # Handle calculation of first birth timing and of marriage ages
    events.new <- calc_first_birth_time(c("First birth", "Marriage"), events_data)
    events.new <- cbind(events.new, runname=rep(runname, nrow(events.new)))

    # Merge the land cover type data so results can be plotted by cover class
    events.new <- merge(events.new, lcdata)

    if (n==1) {events <- events.new}
    else {events <- rbind(events, events.new)}
 
    ###########################################################################
    # Handle calculation of change in land use (aggregated)
    lulc.new <- calc_agg_LULC(results, time_values)
    names(lulc.new) <- paste(names(lulc.new), runname, sep=".")

    if (n==1) lulc_agg <- lulc.new 
    else lulc_agg <- cbind(lulc_agg, lulc.new)

    ###########################################################################
    # Handle calculation of neighborhood-level land use change
    lulc_cols <- grep('^(agveg|nonagveg|pubbldg|privbldg|other).[0-9]*$', 
                      names(results))
    nbh_area <- apply(cbind(results$agveg.1, results$nonagveg.1, results$pubbldg.1,
            results$privbldg.1, results$other.1), 1, sum)
    lulc_nbh.new <- data.frame(nid=results$neighid, nbh_area=nbh_area, run=runname, results[lulc_cols])

    if (n==1) lulc_nbh <- lulc_nbh.new 
    else lulc_nbh <- rbind(lulc_nbh.new, lulc_nbh.new)

    ###########################################################################
    # Handle calculation of rate of change of land use
    lulc_rtchange.new <- calc_rate_change_agveg(directory)
    lulc_rtchange.new$run <- runname

    if (n==1) lulc_rtchange <- lulc_rtchange.new 
    else lulc_rtchange <- rbind(lulc_rtchange, lulc_rtchange.new)

    ###########################################################################
    # Handle calculation of neighborhood-level population characteristics
    pop_results.new <- calc_NBH_pop(results, time_values)
    names(pop_results.new) <- paste(names(pop_results.new), runname, sep=".")

    if (n==1) pop_results <- pop_results.new 
    else pop_results <- cbind(pop_results, pop_results.new)

    n <- n + 1
}

###########################################################################
# Copy some miscellaneous files to the main model output folder
###########################################################################
flag <- file.copy(paste(directories[1], "chitwanabm_world_mask.tif", sep="/"), 
                  paste(DATA_PATH, "chitwanabm_world_mask.tif", sep="/"))

DATA_PATH <- "M:/Data/Nepal/chitwanabm_runs/Testing"
# Save neighborhoods coordinates into the main scenario path for later reuse.
NBHs_end <- read.csv(paste(directories[1], "NBHs_time_END.csv", sep="/"))
NBH_coords <- NBHs_end[grep('^(nid)|(rid)|(x)|(y)$', names(NBHs_end))]
save(NBH_coords, file=paste(DATA_PATH, "NBH_coords.Rdata", sep="/"))

save(time_values, file=paste(DATA_PATH, "time_values.Rdata", sep="/"))

###########################################################################
# Output data, as Rdata files to save space
###########################################################################
#save(nbh_coords, file=paste(DATA_PATH, "nbh_coords.Rdata", sep="/"))
save(lcdata, file=paste(DATA_PATH, "lcdata.Rdata", sep="/"))
save(marriage_events, file=paste(DATA_PATH, "marriage_events.Rdata", sep="/"))
save(events, file=paste(DATA_PATH, "events.Rdata", sep="/"))
save(lulc_agg, file=paste(DATA_PATH, "lulc_agg.Rdata", sep="/"))
save(lulc_rtchange, file=paste(DATA_PATH, "lulc_rtchange.Rdata", sep="/"))
save(lulc_nbh, file=paste(DATA_PATH, "lulc_nbh.Rdata", sep="/"))
save(pop_results, file=paste(DATA_PATH, "pop_results.Rdata", sep="/"))
