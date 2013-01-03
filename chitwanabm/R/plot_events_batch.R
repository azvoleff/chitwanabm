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
library(gstat)
library(rgdal)
library(reshape)
library(grid) # for 'unit' function
library(RColorBrewer) # for 'unit' function

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

calc_event_data <- function(event_type, run_path) {
    events_data <- read.csv(paste(run_path, "person_events.log", sep="/"), na.strings=c("NA", "None"))
    events <- events_data[grep('^(nid|time|event)$', names(events_data))]
    events <- events[events$event == event_type, ]
    events <- merge(events, time_values, by.x="time", by.y="timestep")
    events <- cbind(events, ones=rep(1, nrow(events)))
    event_count <- aggregate(events$ones, by=list(neighid=events$nid, year=events$year), sum)
    names(event_count)[grep('^x$', names(event_count))] <- 'num_events'
    # If event_type is Marriage, there is one row per new spouse, so the number 
    # of events needs to be halved to get the number of new marriages.
    if (event_type == "Marriage") event_count$num_events <- event_count$num_events / 2

    # Normalize events by population of village during that year (using the 
    # population in the first month of the year the events occurred).
    results <- read.csv(paste(run_path, "run_results.csv", sep="/"))
    num_psn_cols <- grep('^num_psn.', names(results))
    neigh_pop_cols <- grep('^(neighid|num_psn.)', names(results))
    neigh_pop <- reshape(results[neigh_pop_cols], direction="long", 
                            idvar="neighid", varying=c(2:ncol(results[neigh_pop_cols])))
    neigh_pop$year <- floor(1997 + (neigh_pop$time-1)/12)
    nbh_pop <- neigh_pop$num_psn[match(paste(event_count$neighid, 
                                             event_count$year), 
                                       paste(neigh_pop$neighid, 
                                             neigh_pop$year))]
    event_count$num_events_crude_rate <- (event_count$num_events/nbh_pop) * 1000

    return(event_count)
}

event_type <- "Marriage"
n <- 1
for (directory in directories) {
    possible_error <- tryCatch(events.new <- calc_event_data(event_type, directory), 
                               error=function(e) e)
    # Catch cases where results file does not exist (because run was 
    # interrupted, run is not yet finished, etc.)
    if (inherits(possible_error, "error")) {
        warning(paste("Error reading", directory))
        next
    }
    runname <- paste("run", n, sep="")
    num_events_cols <- grep('num_events', names(events.new))
    names(events.new)[num_events_cols] <- paste(names(events.new[num_events_cols]), runname, sep=".")
    if (n==1) {events <- events.new}
    else {events <- merge(events, events.new, all=TRUE)}
    n <- n + 1
}
events <- events[order(events$neighid, events$year), ]

# Merge a full nbhs x timesteps dataframe so we can fill in zeros in months 
# with no events.
initial_year <- time_values[time_values$timestep == 1, ]$year
final_year <- time_values[time_values$timestep == max(time_values$timestep), ]$year
all_nbhs_timsteps <- data.frame(neighid=gl(151, final_year - initial_year + 1), 
                               year=rep(seq(initial_year, final_year), 151))
events <- merge(events, all_nbhs_timsteps, all=TRUE)
events[is.na(events)] <- 0

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
events <- merge(events, cover_types)

# Save num_marr for later kriging
num_events_cols <- grep('num_events[.]', names(events))
num_marr <- aggregate(events[num_events_cols], by=list(neighid=events$neighid), sum)
num_marr <- data.frame(neighid=num_marr$neighid, num_marr=apply(num_marr[-1], 1, mean))

crude_rate_cols <- grep('num_events_crude_rate.', names(events))
run_means <- aggregate(events[crude_rate_cols], by=list(year=events$year, lctype=events$lctype), mean)
mean_cols <- grep('num_events_crude_rate.', names(run_means))
means <- data.frame(year=run_means$year, lctype=run_means$lctype, 
                    marriages.mean=apply(run_means[mean_cols], 1, mean))
                  
means$marriages.sd <- apply(run_means[mean_cols], 1, sd)
means$year <- as.Date(as.character(means$year), format="%Y")

write.csv(means, file=paste(DATA_PATH, "ens_results_marriage_rates.csv", sep="/"), row.names=FALSE)

p <- ggplot()
p + geom_line(aes(year, marriages.mean, colour=lctype), data=means) +
    geom_ribbon(aes(x=year, ymin=(marriages.mean - marriages.sd *2 ), 
                    ymax=(marriages.mean + marriages.sd * 2), fill=lctype), 
                alpha=.2, data=means) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Rate (per 1000)', colour="Cover Class")
ggsave(paste(DATA_PATH, "num_marriage_events.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

# Drop mixed classes:
means <- means[!grepl('(Semi-urban|Semi-agricultural)', means$lctype), ]
p <- ggplot()
p + geom_line(aes(year, marriages.mean, colour=lctype), data=means) +
    geom_ribbon(aes(x=year, ymin=(marriages.mean - marriages.sd *2 ), 
                    ymax=(marriages.mean + marriages.sd * 2), fill=lctype), 
                alpha=.2, data=means) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Rate (per 1000)', colour="Cover Class")
ggsave(paste(DATA_PATH, "num_marriage_events_2_class.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

###############################################################################
# Now make a map of kriged 
# Load the grid on which to Krige. This GeoTIFF also will be used to mask the 
# final kriging results.
world_mask <- paste(directories[1], "chitwanabm_world_mask.tif", sep="/")
kriglocations <- readGDAL(world_mask)
kriglocations$band1[kriglocations$band1==min(kriglocations$band1)] <- 0
kriglocations$band1[kriglocations$band1==max(kriglocations$band1)] <- 1

NBHs <- read.csv(paste(directories[1], "/NBHs_time_END.csv", sep=""))
NBHs <- merge(NBHs, num_marr, by.x="nid", by.y="neighid")
NBHs.spatial <- SpatialPointsDataFrame(cbind(NBHs$x, NBHs$y), NBHs,
        coords.nrs=c(3,4), proj4string=CRS(proj4string(kriglocations)))

# Use ordinary kriging
v <- variogram(num_marr~1, NBHs.spatial)
#v.fit <- fit.variogram(v, vgm(1, "Exp", 6000, .05))
v.fit <- fit.variogram(v, vgm(1, "Sph", 6000, .05))
krigged.ord <- krige(num_marr ~ 1, NBHs.spatial, kriglocations, v.fit)

krigged.ord.pred <- krigged.ord["var1.pred"]
# Mask out areas outside Chitwan using the study area mask. Set areas outside 
# study area to -999
krigged.ord.pred$var1.pred <- krigged.ord.pred$var1.pred * kriglocations$band1
krigged.ord.pred$var1.pred[krigged.ord.pred$var1.pred==0] <- -1
proj4string(krigged.ord.pred) <- CRS(proj4string(kriglocations))
krigged_imagefile <- paste(DATA_PATH, "/num_marriages_ordinary_krig_END.tif", sep="")
writeGDAL(krigged.ord.pred, fname=krigged_imagefile, driver="GTiff")

###############################################################################
# Check the kriging results with cross-validation
krigged.ord.cv5 <- krige.cv(num_marr~1, NBHs.spatial, v.fit, nfold=5)
# correlation observed and predicted, ideally 1
cor.obs.pred <- cor(krigged.ord.cv5$observed,
        krigged.ord.cv5$observed - krigged.ord.cv5$residual)
# Mean error, ideally 0:
mean.residual <- mean(krigged.ord.cv5$residual)
# correlation predicted and residual, ideally 0
cor.pred.resid <- cor(krigged.ord.cv5$observed - krigged.ord.cv5$residual,
        krigged.ord.cv5$residual)

# Setup the plot annotation
xcoord <- 816000
ycoord <- 3068000
deltay <- -1000
i1 <- list("sp.text", c(xcoord, ycoord),
                format(paste("Mean Resid.:", round(mean.residual, 4)), width=30))
ycoord <- ycoord + deltay
i2 <- list("sp.text", c(xcoord, ycoord),
                format(paste("Cor. Obs. Pred.:", round(cor.obs.pred, 4)), width=30))
ycoord <- ycoord + deltay
i3 <- list("sp.text", c(xcoord, ycoord),
                format(paste("Cor. Pred. Resid.:",  round(cor.pred.resid, 4)), width=30))
ycoord <- ycoord + deltay
bubble_imagefile <- paste(DATA_PATH, "/num_marriages_ordinary_krig_END_bubble.png", sep="")
png(filename=bubble_imagefile, width=8.33, height=5.33, units="in", res=300)
bubble(krigged.ord.cv5, "residual", main="Crossvalidation Residuals",
        maxsize=2, col=c("blue", "red"), sp.layout=list(i1, i2, i3),
        key.entries=c(-.5, -.25, -.1, .1, .25, .5))
dev.off()
