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
library(gstat)
library(rgdal)

PLOT_WIDTH <- 8.33
PLOT_HEIGHT <- 5.53
DPI <- 300

initial.options <- commandArgs(trailingOnly = FALSE)
file.arg.name <- "--file="
script.name <- sub(file.arg.name, "", initial.options[grep(file.arg.name, initial.options)])
script.basename <- dirname(script.name)
source(paste(script.basename, "calc_NBH_stats.R", sep="/"))

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
DATA_PATH <- "M:/Data/Nepal/chitwanabm_runs/20130101_ES_Paper_Scenarios/to 2020/Half_Feedbacks_firstbirthscenarios"
DATA_PATH <- "M:/Data/Nepal/chitwanabm_runs/20130101_ES_Paper_Scenarios/to 2020/Half_Feedbacks_marriagescenarios"
DATA_PATH <- "M:/Data/Nepal/chitwanabm_runs/20130101_ES_Paper_Scenarios/to 2020/No_Feedbacks_firstbirthscenarios"

###########################################################################
# Helper functions
###########################################################################

###########################################################################
# Plot population characteristics
###########################################################################
load(file=paste(DATA_PATH, "pop_results.Rdata", sep="/"))
ens_results <- calc_ensemble_results(pop_results)
save(ens_results, file=paste(DATA_PATH, "ens_results_pop.Rdata", sep="/"))
write.csv(ens_results, file=paste(DATA_PATH, "ens_results_pop.csv", sep="/"), row.names=FALSE)

# First plot monthly event data
# Column 1 is times, so that column is always needed
events <- ens_results[c(1, grep("^(marr|births|deaths)", names(ens_results)))]
make_shaded_error_plot(events, "Number of Events", "Event Type")
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
