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
# Initialize variables and packages, and setup plotting defaults.
###############################################################################

library(ggplot2)
library(reshape)
library(gstat)
library(rgdal)
library(lubridate)

PLOT_WIDTH <- 8.33
PLOT_HEIGHT <- 5.53
DPI <- 300

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

###########################################################################
# Helper functions
###########################################################################
calc_ensemble_results <- function(model_results) {
    # The first column of model_results dataframe should be the times
    # For each variable listed in "variable_names", there should be two columns,
    # one of means, named "variable_name.mean" and one of standard deviations,
    # named "variable_name.sd"
    var_names <- unique(gsub(".run[0-9]*$", "",
                    names(model_results)[2:ncol(model_results)]))
    var_names <- var_names[var_names!="time.Robj"]

    # First calculate the mean and standard deviations for each set of runs
    ens_res <- data.frame(time.Robj=model_results$time.Robj.run1)
    for (var_name in var_names) {
        var_cols <- grep(paste("^", var_name, ".", sep=""), names(model_results))
        var_mean <- apply(model_results[var_cols], 1, mean)
        var_sd <- apply(model_results[var_cols], 1, sd)
        ens_res <- cbind(ens_res, var_mean, var_sd)
        var_mean.name <- paste(var_name, ".mean", sep="")
        var_sd.name <- paste(var_name, ".sd", sep="")
        names(ens_res)[(length(ens_res)-1):length(ens_res)] <- c(var_mean.name, var_sd.name)
    }
    ens_res <- ens_res[ens_res$time.Robj>"1997-01-01", ]
    return(ens_res)
}

make_shaded_error_plot <- function(ens_res, ylabel, typelabel) {
    # The first column of ens_res dataframe should be the times
    # For each variable listed in "variable_names", there should be two columns,
    # one of means, named "variable_name.mean" and one of standard deviations,
    # named "variable_name.sd"
    theme_set(theme_grey(base_size=18))
    update_geom_defaults("line", aes(size=1))

    # Ignore column one in code in next line since it is only the time
    var_names <- unique(gsub("(.mean)|(.sd)", "",
                    names(ens_res)[2:ncol(ens_res)]))
    num_vars <- length(var_names)
    time.Robj <- ens_res$time.Robj

    # Stack the data to use in ggplot2
    mean.cols <- grep("(^time.Robj$)|(.mean$)", names(ens_res))
    sd.cols <- grep(".sd$", names(ens_res))
    ens_res.mean <- melt(ens_res[mean.cols], id.vars="time.Robj")
    names(ens_res.mean)[2:3] <- c("Type", "mean")
    # Remove the ".mean" appended to the Type values (agveg.mean, 
    # nonagveg.mean, etc) so that it does not appear in the plot legend.
    ens_res.mean$Type <- gsub(".mean", "", ens_res.mean$Type)

    sd.cols <- grep("(^time.Robj$)|(.sd$)", names(ens_res))
    ens_res.sd <- melt(ens_res[sd.cols], id.vars="time.Robj")
    names(ens_res.sd)[2:3] <- c("Type", "sd")

    # Add lower and upper limits of ribbon to ens_res.sd dataframe
    ens_res.sd <- cbind(ens_res.sd, lim.up=ens_res.mean$mean + 2*ens_res.sd$sd)
    ens_res.sd <- cbind(ens_res.sd, lim.low=ens_res.mean$mean - 2*ens_res.sd$sd)

    p <- ggplot()
    if (is.na(typelabel)) {
        # Don't use types - used for plotting things like fuelwood and total 
        # populatation, where there is only one class on the plot.
        p + geom_line(aes(time.Robj, mean), data=ens_res.mean) +
            geom_ribbon(aes(x=time.Robj, ymin=lim.low, ymax=lim.up),
                alpha=.2, data=ens_res.sd) +
            scale_fill_discrete(guide='none') +
            labs(x="Years", y=ylabel)
    }
    else {
        p + geom_line(aes(time.Robj, mean, colour=Type), data=ens_res.mean) +
            geom_ribbon(aes(x=time.Robj, ymin=lim.low, ymax=lim.up, fill=Type),
                alpha=.2, data=ens_res.sd) +
            scale_fill_discrete(guide='none') +
            labs(x="Years", y=ylabel, colour=typelabel)
    }
}

###########################################################################
# Plot population characteristics
###########################################################################
load(file=paste(DATA_PATH, "pop_results.Rdata", sep="/"))
ens_results <- calc_ensemble_results(pop_results)
save(ens_results, file=paste(DATA_PATH, "ens_results_pop.Rdata", sep="/"))
write.csv(ens_results, file=paste(DATA_PATH, "ens_results_pop.csv", sep="/"), row.names=FALSE)

# First plot monthly event data
# Column 1 is times, so that column is always needed
pop_events <- ens_results[c(1, grep("^(marr|births|deaths)", names(ens_results)))]
make_shaded_error_plot(pop_events, "Number of Events", "Event Type")
ggsave(paste(DATA_PATH, "pop_events.png", sep="/"), width=PLOT_WIDTH, height=PLOT_HEIGHT,
        dpi=DPI)

# Now plot total households and total marriages
num.hs.marr <- ens_results[c(1, grep("^(num_marr|num_hs)", names(ens_results)))]
make_shaded_error_plot(num.hs.marr, "Number", "Type")
ggsave(paste(DATA_PATH, "pop_num_hs_marr.png", sep="/"), width=PLOT_WIDTH, height=PLOT_HEIGHT,
        dpi=DPI)

# Plot total population
num_psn <- ens_results[c(1, grep("^(num_psn)", names(ens_results)))]
make_shaded_error_plot(num_psn, "Total Population", NA)
ggsave(paste(DATA_PATH, "pop_num_psn.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=DPI)

# Plot fw consumption in metric tons
fw_usage <- ens_results[c(1, grep("^(fw_usage)", names(ens_results)))]
# fw consumption is in tons per person per month
fw_usage$fw_usage_metrictons.mean <- fw_usage$fw_usage_kg.mean/1000
fw_usage$fw_usage_metrictons.sd <- fw_usage$fw_usage_kg.sd/1000
fw_usage <- fw_usage[!grepl("kg", names(fw_usage))]
make_shaded_error_plot(fw_usage, "Metric Tons of Fuelwood", NA)
ggsave(paste(DATA_PATH, "fw_usage.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)
write.csv(fw_usage, file=paste(DATA_PATH, "fw_usage_ens_results.csv", sep="/"), row.names=FALSE)

###########################################################################
# Plot aggregate land use
###########################################################################
load(file=paste(DATA_PATH, "lulc_agg.Rdata", sep="/"))

ens_results <- calc_ensemble_results(lulc_agg)
save(ens_results, file=paste(DATA_PATH, "ens_results_LULC.Rdata", sep="/"))
write.csv(ens_results, file=paste(DATA_PATH, "ens_results_LULC.csv", sep="/"))

make_shaded_error_plot(ens_results, "Mean Percentage of Neighborhood", "LULC Type")
ggsave(paste(DATA_PATH, "batch_LULC.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=DPI)

###########################################################################
# Plot rate of change of agricultural vegetation
###########################################################################
load(file=paste(DATA_PATH, "lulc_rtchange.Rdata", sep="/"))

lulc_rtchange$agveg_changepct <- (lulc_rtchange$agveg_change / lulc_rtchange$nbh_area) * 100
lulc_rtchange$year <- as.Date(cut(lulc_rtchange$time.Robj, "year"))
lulc_rtchange$lctype <- cut(lulc_rtchange$agveg, quantile(lulc_rtchange$agveg), labels=c('Urban', 
                                                              'Semi-urban', 
                                                              'Semi-agricultural', 
                                                              'Agricultural'))
lulc_rtchange$lctype[is.na(lulc_rtchange$lctype)] <- levels(lulc_rtchange$lctype)[1]

# Convert agricultural vegetation areal units from square meters to hectares
lulc_rtchange$agveg_change_ha <- lulc_rtchange$agveg_change * .0001
agveg_annual_change <-  aggregate(lulc_rtchange$agveg_change_ha,
                          by=list(time.Robj=lulc_rtchange$year, nid=lulc_rtchange$nid, 
                                  lctype=lulc_rtchange$lctype), sum)
names(agveg_annual_change)[grep('^x$', names(agveg_annual_change))] <- 'agveg_change_ha'
agveg_change_ha_means <- aggregate(agveg_annual_change$agveg_change_ha, 
                                   by=list(time.Robj=agveg_annual_change$time.Robj, 
                                   lctype=agveg_annual_change$lctype), 
                                   mean)
names(agveg_change_ha_means)[grep('^x$', names(agveg_change_ha_means))] <- 'agveg_change_ha.mean'
agveg_change_ha_means.sd <- aggregate(agveg_annual_change$agveg_change_ha,
                                      by=list(time.Robj=agveg_annual_change$time.Robj, 
                                              lctype=agveg_annual_change$lctype), 
                                      sd)
names(agveg_change_ha_means.sd)[grep('^x$', names(agveg_change_ha_means.sd))] <- 'agveg_change_ha.sd'
agveg_change_ha_means <- merge(agveg_change_ha_means, agveg_change_ha_means.sd)

p <- ggplot()
p + geom_line(aes(time.Robj, agveg_change_ha.mean, colour=lctype), data=agveg_change_ha_means) +
    geom_ribbon(aes(x=time.Robj, ymin=(agveg_change_ha.mean - 2 * agveg_change_ha.sd), 
                    ymax=(agveg_change_ha.mean + 2 * agveg_change_ha.sd), fill=lctype),
        alpha=.2, data=agveg_change_ha_means) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Mean Annual Change in Agricultural Veg. (hectares)', colour="Initial Land-use Class")
ggsave(paste(DATA_PATH, "lulc_agveg_change_ha.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=DPI)
save(agveg_change_ha_means, file=paste(DATA_PATH, "ens_results_LULC_change.Rdata", sep="/"))
write.csv(agveg_change_ha_means, file=paste(DATA_PATH, "ens_results_LULC_change.csv", sep="/"))

###########################################################################
# Now make a map of kriged land cover for the final timestep
###########################################################################

# First load the grid on which to Krige. This GeoTIFF also will be used to mask 
# the final kriging results. The world mask can be loaded from any of the 
# chitwanabm model output folders (they all should match since they all should 
# represent the same scenario).
world_mask_file <- paste(DATA_PATH, "chitwanabm_world_mask.tif", sep="/")
kriglocations <- readGDAL(world_mask_file)
if (length(unique(kriglocations$band1)) != 2) stop("ERROR: chitwanabm_world_mask.tif is not a binary raster")
kriglocations$band1[kriglocations$band1==min(kriglocations$band1)] <- 0
kriglocations$band1[kriglocations$band1==max(kriglocations$band1)] <- 1

# TODO: For now, load the recoded NBH data to get the NBH coordinates. These 
# coordinates should be loaded directly from the model - they should be stored 
# in the model results.
load("V:/Nepal/ICPSR_0538_Restricted/Recode/recoded_NBH_data.Rdata")
NBH_LULC <- data.frame(nid=as.numeric(nbh_recode$NEIGHID), x=nbh_recode$NX, y=nbh_recode$NY)
NBH_LULC <- NBH_LULC[NBH_LULC$nid <= 151, ]

load(file=paste(DATA_PATH, "lulc_nbh.Rdata", sep="/"))
load(file=paste(DATA_PATH, "time_values.Rdata", sep="/"))

agveg_final_col <- grep(paste('^agveg.', max(time_values$timestep), sep=''), 
                        names(lulc_nbh))
lulc_nbh$final_agvegpct <- (lulc_nbh[, agveg_final_col] / lulc_nbh$nbh_area) * 100
mean_agveg <- aggregate(lulc_nbh$final_agvegpct, by=list(lulc_nbh$nid), mean)
NBH_LULC$agveg_final_pct.mean <- mean_agveg$x

NBH_LULC.spatial <- SpatialPointsDataFrame(cbind(NBH_LULC$x, NBH_LULC$y), NBH_LULC,
        coords.nrs=c(3,4), proj4string=CRS(proj4string(kriglocations)))

# Use ordinary kriging
v <- variogram(agveg_final_pct.mean~1, NBH_LULC.spatial)
v.fit <- fit.variogram(v, vgm(1, "Exp", 6000, .05))
v.fit <- fit.variogram(v, vgm(1, "Sph", 6000, .05))
krigged.ord <- krige(agveg_final_pct.mean~1, NBH_LULC.spatial, kriglocations, v.fit)

krigged.ord.pred <- krigged.ord["var1.pred"]
# Mask out areas outside Chitwan using the study area mask. Set areas outside 
# study area to -999
krigged.ord.pred$var1.pred <- krigged.ord.pred$var1.pred * kriglocations$band1
krigged.ord.pred$var1.pred[krigged.ord.pred$var1.pred==0] <- -1
proj4string(krigged.ord.pred) <- CRS(proj4string(kriglocations))
writeGDAL(krigged.ord.pred, fname=paste(DATA_PATH, "batch_LULC_ordinary_krig_endofrun.tif",
        sep="/"), driver="GTiff")

classed <- krigged.ord.pred
classed$var1.pred[classed$var1.pred >= .75] <- 4
classed$var1.pred[classed$var1.pred >= .5 & classed$var1.pred <.75] <- 3
classed$var1.pred[classed$var1.pred >= .25 & classed$var1.pred <.5] <- 2
classed$var1.pred[classed$var1.pred >= 0 & classed$var1.pred <.25] <- 1
writeGDAL(classed, fname=paste(DATA_PATH,
        "batch_LULC_ordinary_krig_endofrun_classed.tif", sep="/"), driver="GTiff")

###############################################################################
# Check the kriging results with cross-validation
krigged.ord.cv5 <- krige.cv(agveg_final_pct.mean~1, NBH_LULC.spatial, v.fit, nfold=5)
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
png(filename=paste(DATA_PATH, "batch_LULC_ordinary_krig_endofrun_bubble.png", sep="/"),
        width=8.33, height=5.33, units="in", res=DPI)
bubble(krigged.ord.cv5, "residual", main="Crossvalidation Residuals",
        maxsize=2, col=c("blue", "red"), sp.layout=list(i1, i2, i3),
        key.entries=c(-.5, -.25, -.1, .1, .25, .5))
dev.off()

###########################################################################
# Make plots of marriage rates
###########################################################################
load(file=paste(DATA_PATH, "marriage_events.Rdata", sep="/"))
marriage_events$neighid <- as.integer(marriage_events$neighid)
marriage_events <- marriage_events[order(marriage_events$neighid, marriage_events$year), ]

# Merge a full nbhs x timesteps dataframe so we can fill in zeros in months 
# with no events.
initial_year <- min(marriage_events$year)
final_year <- max(marriage_events$year)
all_nbhs_timesteps <- data.frame(neighid=gl(151, final_year - initial_year + 1), 
                               year=rep(initial_year, final_year, 151))
marriage_events <- merge(marriage_events, all_nbhs_timesteps, all=TRUE)
marriage_events[is.na(marriage_events)] <- 0

load(paste(DATA_PATH, "lcdata.Rdata", sep="/"))
# Merge the initial cover types so results can be plotted by cover class
lctype <- cut(lcdata$pctagveg.initial, quantile(lcdata$pctagveg.initial), 
                      labels=c('Urban', 'Semi-urban', 'Semi-agricultural', 
                               'Agricultural'))
lctype[is.na(lctype)] <- levels(lctype)[1]
cover_types <- data.frame(neighid=lcdata$nid, lctype=lctype)
marriage_events <- merge(marriage_events, cover_types)

# # Save num_marr for later kriging
# num_events_cols <- grep('num_events[.]', names(marriage_events))
# num_marr <- aggregate(marriage_events[num_events_cols], by=list(neighid=marriage_events$neighid), sum)
# num_marr <- data.frame(neighid=num_marr$neighid, num_marr=apply(num_marr[-1], 1, mean))
 
crude_rate_cols <- grep('num_events_crude_rate.', names(marriage_events))
marriage_run_means <- aggregate(marriage_events[crude_rate_cols], by=list(year=marriage_events$year, lctype=marriage_events$lctype), mean)
mean_cols <- grep('num_events_crude_rate.', names(marriage_run_means))
marriage_means <- data.frame(year=marriage_run_means$year, lctype=marriage_run_means$lctype, 
                    marriages.mean=apply(marriage_run_means[mean_cols], 1, mean))
marriage_means$marriages.sd <- apply(marriage_run_means[mean_cols], 1, sd)
marriage_means$time.Robj <- floor_date(as.Date(as.character(marriage_means$year), format="%Y"), "year")
write.csv(marriage_means, file=paste(DATA_PATH, "ens_results_marriage_rates.csv", sep="/"), row.names=FALSE)

p <- ggplot()
p + geom_line(aes(time.Robj, marriages.mean, colour=lctype), data=marriage_means) +
    geom_ribbon(aes(x=time.Robj, ymin=(marriages.mean - marriages.sd *2 ), 
                    ymax=(marriages.mean + marriages.sd * 2), fill=lctype), 
                alpha=.2, data=marriage_means) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Rate (per 1000)', colour="Cover Class")
ggsave(paste(DATA_PATH, "num_marriage_events.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)

# Drop mixed classes:
marriage_means_2class <- marriage_means[!grepl('(Semi-urban|Semi-agricultural)', marriage_means$lctype), ]
p <- ggplot()
p + geom_line(aes(time.Robj, marriages.mean, colour=lctype), data=marriage_means_2class) +
    geom_ribbon(aes(x=time.Robj, ymin=(marriages.mean - marriages.sd *2 ), 
                    ymax=(marriages.mean + marriages.sd * 2), fill=lctype), 
                alpha=.2, data=marriage_means_2class) +
    scale_fill_discrete(guide='none') +
    labs(x="Years", y='Marriage Rate (per 1000)', colour="Cover Class")
ggsave(paste(DATA_PATH, "num_marriage_events_2_class.png", sep="/"), width=PLOT_WIDTH, 
       height=PLOT_HEIGHT, dpi=300)


###########################################################################
# Make plots of changes in marriage timing and first birth timing
###########################################################################
load(file=paste(DATA_PATH, "events.Rdata", sep="/"))

# Merge the initial cover types so results can be plotted by cover class
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
fb_int_means$time.Robj <- floor_date(as.Date(as.character(fb_int_means$year), format="%Y"), 'year')
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
marr_age_means$time.Robj <- floor_date(as.Date(as.character(marr_age_means$year), format="%Y"), 'year')

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
