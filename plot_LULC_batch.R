#!/usr/bin/env Rscript
# Plots the LULC data from a model run.
require(ggplot2, quietly=TRUE)
require(gstat)
require(rgdal)

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

directories <- list.files(DATA_PATH)
# Only match the model results folders - don't match any other folders or files 
# in the directory, as trying to read results from these other files/folders 
# would lead to an error.
directories <- directories[grep("[0-9]{8}-[0-9]{6}", directories)]

n <- 1
for (directory in directories) {
    full_directory_path <- paste(DATA_PATH, directory, sep="/") 
    lulc.new <- calc_agg_LULC(full_directory_path)
    runname <- paste("run", n, sep="")
    names(lulc.new) <- paste(names(lulc.new), runname, sep=".")
    if (n==1) lulc.agg <- lulc.new 
    else  lulc.agg <- cbind(lulc.agg, lulc.new)
    n <- n + 1
}

ens_results <- calc_ensemble_results(lulc.agg)


make_shaded_error_plot(ens_results, "Mean Percentage of Neighborhood", "LULC Type")
ggsave(paste(DATA_PATH, "batch_LULC.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)

###############################################################################
# Now make a map of kriged LULC
n <- 1
for (directory in directories) {
    full_directory_path <- paste(DATA_PATH, directory, sep="/") 
    lulc.new <- calc_NBH_LULC(full_directory_path, 276)
    vars <- !grepl('^(nid|x|y)$', names(lulc.new))
    runname <- paste("run", n, sep="")
    names(lulc.new)[vars]<- paste(names(lulc.new)[vars], runname, sep=".")
    if (n==1) {
        names(lulc.new)[grep('nid.run1', names(lulc.new))] <- "nid"
        lulc.nbh <- lulc.new 
    }
    else {
        lulc.new <- lulc.new[-grep('nid', names(lulc.new))]
        lulc.nbh <- cbind(lulc.nbh, lulc.new)
    }
    n <- n + 1
} 

NBH_lulc <- calc_ensemble_results_NBH(lulc.nbh)

CRSString = "+proj=utm +zone=44 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
NBH_lulc.spatial <- SpatialPointsDataFrame(cbind(NBH_lulc$x, NBH_lulc$y), NBH_lulc,
        coords.nrs=c(3,4), proj4string=CRS(CRSString))

# Load the grid on which to Krige. This GeoTIFF also will be used to mask the 
# final kriging results.
kriglocations <- readGDAL("CVFS_Study_Area_Raster.tif")

# Use ordinary kriging
v <- variogram(agveg.mean~1, NBH_lulc.spatial)
v.fit <- fit.variogram(v, vgm(1, "Exp", 6000, .05))
v.fit <- fit.variogram(v, vgm(1, "Sph", 6000, .05))
krigged.ord <- krige(agveg.mean~1, NBH_lulc.spatial, kriglocations, v.fit)

krigged.ord.pred <- krigged.ord["var1.pred"]
# Mask out areas outside Chitwan using the study area mask. Set areas outside 
# study area to -999
krigged.ord.pred$var1.pred <- krigged.ord.pred$var1.pred * kriglocations$band1
krigged.ord.pred$var1.pred[krigged.ord.pred$var1.pred==0] <- -1
proj4string(krigged.ord.pred) <- CRS(CRSString)
writeGDAL(krigged.ord.pred, fname=paste(DATA_PATH, "LULC_ordinary_krig_276.tif",
        sep="/"), driver="GTiff")

classed <- krigged.ord.pred
classed$var1.pred[classed$var1.pred >= .75] <- 4
classed$var1.pred[classed$var1.pred >= .5 & classed$var1.pred <.75] <- 3
classed$var1.pred[classed$var1.pred >= .25 & classed$var1.pred <.5] <- 2
classed$var1.pred[classed$var1.pred >= 0 & classed$var1.pred <.25] <- 1
writeGDAL(classed, fname=paste(DATA_PATH,
        "LULC_ordinary_krig_276_classed.tif", sep="/"), driver="GTiff")

###############################################################################
# Check the kriging results with cross-validation
krigged.ord.cv5 <- krige.cv(agveg.mean~1, NBH_lulc.spatial, v.fit, nfold=5)
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
png(filename=paste(DATA_PATH, "LULC_ordinary_krig_276_bubble.png", sep="/"),
        width=8.33, height=5.33, units="in", res=300)
bubble(krigged.ord.cv5, "residual", main="Crossvalidation Residuals",
        maxsize=2, col=c("blue", "red"), sp.layout=list(i1, i2, i3))
dev.off()
