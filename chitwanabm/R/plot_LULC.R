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
# Plots the LULC data from a model run.
###############################################################################

library(ggplot2, quietly=TRUE)
library(gstat)
library(rgdal)
library(reshape)
library(grid) # for 'unit' function
library(RColorBrewer) # for 'unit' function

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53

initial.options <- commandArgs(trailingOnly = FALSE)
file.arg.name <- "--file="
script.name <- sub(file.arg.name, "", initial.options[grep(file.arg.name, initial.options)])
script.basename <- dirname(script.name)
source(paste(script.basename, "calc_NBH_stats.R", sep="/"))

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

lulc.sd.mean <- calc_agg_LULC(DATA_PATH)
lulc.sd.mean <- melt(lulc.sd.mean, id.vars="time.Robj")
names(lulc.sd.mean)[2:3] <- c("LULC_type", "area")

# Now actually make the plots
theme_update(theme_grey(base_size=16))
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
    opts(legend.key.width=unit(1, "cm"))

ggsave(paste(DATA_PATH, "LULC.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)

###############################################################################
# Now make a map of kriged LULC
# Load the grid on which to Krige. This GeoTIFF also will be used to mask the 
# final kriging results.
world_mask <- paste(DATA_PATH, "chitwanabm_world_mask.tif", sep="/")
kriglocations <- readGDAL(world_mask)
kriglocations$band1[kriglocations$band1==min(kriglocations$band1)] <- 0
kriglocations$band1[kriglocations$band1==max(kriglocations$band1)] <- 1

NBHs <- read.csv(paste(DATA_PATH, "/NBHs_time_END.csv", sep=""))
NBHs.spatial <- SpatialPointsDataFrame(cbind(NBHs$x, NBHs$y), NBHs,
        coords.nrs=c(3,4), proj4string=CRS(proj4string(kriglocations)))

# Use ordinary kriging
v <- variogram(perc_veg~1, NBHs.spatial)
#v.fit <- fit.variogram(v, vgm(1, "Exp", 6000, .05))
v.fit <- fit.variogram(v, vgm(1, "Sph", 6000, .05))
krigged.ord <- krige(perc_veg~1, NBHs.spatial, kriglocations, v.fit)

krigged.ord.pred <- krigged.ord["var1.pred"]
# Mask out areas outside Chitwan using the study area mask. Set areas outside 
# study area to -999
krigged.ord.pred$var1.pred <- krigged.ord.pred$var1.pred * kriglocations$band1
krigged.ord.pred$var1.pred[krigged.ord.pred$var1.pred==0] <- -1
proj4string(krigged.ord.pred) <- CRS(proj4string(kriglocations))
krigged_imagefile <- paste(DATA_PATH, "/LULC_ordinary_krig_END.tif", sep="")
writeGDAL(krigged.ord.pred, fname=krigged_imagefile, driver="GTiff")

classed <- krigged.ord.pred
classed$var1.pred[classed$var1.pred >= .75] <- 4
classed$var1.pred[classed$var1.pred >= .5 & classed$var1.pred <.75] <- 3
classed$var1.pred[classed$var1.pred >= .25 & classed$var1.pred <.5] <- 2
classed$var1.pred[classed$var1.pred >= 0 & classed$var1.pred <.25] <- 1
krigged_classed_imagefile <- paste(DATA_PATH, "/LULC_ordinary_krig_END_classed.tif", sep="")
writeGDAL(classed, fname=krigged_classed_imagefile, driver="GTiff")
        
###############################################################################
# Check the kriging results with cross-validation
krigged.ord.cv5 <- krige.cv(perc_veg~1, NBHs.spatial, v.fit, nfold=5)
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
bubble_imagefile <- paste(DATA_PATH, "/LULC_ordinary_krig_END_bubble.png", sep="")
png(filename=bubble_imagefile, width=8.33, height=5.33, units="in", res=300)
bubble(krigged.ord.cv5, "residual", main="Crossvalidation Residuals",
        maxsize=2, col=c("blue", "red"), sp.layout=list(i1, i2, i3),
        key.entries=c(-.5, -.25, -.1, .1, .25, .5))
dev.off()

###############################################################################
# Plot the transition matrix
run_results <- read.csv(paste(DATA_PATH, "/run_results.csv", sep=""))
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
