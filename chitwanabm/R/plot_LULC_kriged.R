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

###############################################################################
# Plots kriged map of LULC data from a model run.
###############################################################################

library(gstat)
library(rgdal)

initial.options <- commandArgs(trailingOnly = FALSE)
file.arg.name <- "--file="
script.name <- sub(file.arg.name, "", initial.options[grep(file.arg.name, initial.options)])
script.basename <- dirname(script.name)
source(paste(script.basename, "calc_NBH_stats.R", sep="/"))

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
if (is.na(DATA_PATH)) stop("Data path must be supplied")

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
