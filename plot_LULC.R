#!/usr/bin/env Rscript
# Plots the LULC data from a model run.

require(ggplot2, quietly=TRUE)
require(gstat)
require(rgdal)

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

lulc.sd.mean <- calc_NBH_LULC(DATA_PATH)
# Stack lulc.mean so it can easily be used with ggplot2 faceting
time.Robj <- lulc.sd.mean$time.Robj
lulc.sd.mean <- stack(lulc.sd.mean)
lulc.sd.mean <- cbind(time.Robj=rep(time.Robj,5), lulc.sd.mean)
names(lulc.sd.mean)[2:3] <- c("area", "LULC_type")

# Now actually make the plots
theme_update(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=1))

qplot(time.Robj, area, geom="line", colour=LULC_type, xlab="Year",
        ylab="Mean Percentage of Neighborhood", data=lulc.sd.mean)
ggsave(paste(DATA_PATH, "LULC.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)

# Now make a map of kriged LULC
CRSString = "+proj=utm +zone=44 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
NBHs <- read.csv(paste(DATA_PATH, "NBHs_time_276.csv", sep="/"))
NBHs <- read.csv(paste(DATA_PATH, "NBHs_time_1.csv", sep="/"))
NBHs.spatial <- SpatialPointsDataFrame(cbind(NBHs$x, NBHs$y), NBHs,
        coords.nrs=c(3,4), proj4string=CRS(CRSString))

# Load the grid on which to Krige. This GeoTIFF also will be used to mask the 
# final kriging results.
kriglocations <- readGDAL("CVFS_Study_Area_Raster.tif")

#xs = seq(min(NBHs$x), max(NBHs$x), CELL_SIZE)
#ys = seq(min(NBHs$y), max(NBHs$y), CELL_SIZE)
#kriglocations <- expand.grid(x=xs, y=ys)
#coordinates(kriglocations) <- ~x+y
#gridded(kriglocations) <- TRUE

#krigged.idw.pred <- krige(perc_veg~1, NBHs.spatial, kriglocations)["var1.pred"]
#proj4string(krigged.idw.pred) <- CRS(CRSString)
#writeGDAL(krigged.idw.pred, fname=paste(DATA_PATH, "LULC_IDW.tif", sep="/"), driver="GTiff")

# Use ordinary kriging
v <- variogram(perc_veg~1, NBHs.spatial)
v.fit <- fit.variogram(v, vgm(1, "Exp", 6000, .05))
v.fit <- fit.variogram(v, vgm(1, "Sph", 6000, .05))
krigged.ord <- krige(perc_veg~1, NBHs.spatial, kriglocations, v.fit)

krigged.ord.pred <- krigged.ord["var1.pred"]
# Mask out areas outside Chitwan using the study area mask. Set areas outside 
# study area to -999
krigged.ord.pred$var1.pred <- krigged.ord.pred$var1.pred * kriglocations$band1
krigged.ord.pred$var1.pred[krigged.ord.pred$var1.pred==0] <- -1
proj4string(krigged.ord.pred) <- CRS(CRSString)
writeGDAL(krigged.ord.pred, fname=paste(DATA_PATH, "LULC_ordinary_krig.tif",
        sep="/"), driver="GTiff")

classed <- krigged.ord.pred
classed$var1.pred[classed$var1.pred >= .75] <- 4
classed$var1.pred[classed$var1.pred >= .5 & classed$var1.pred <.75] <- 3
classed$var1.pred[classed$var1.pred >= .25 & classed$var1.pred <.5] <- 2
classed$var1.pred[classed$var1.pred >= 0 & classed$var1.pred <.25] <- 1
writeGDAL(classed, fname=paste(DATA_PATH,
        "LULC_ordinary_krig_classed.tif", sep="/"), driver="GTiff")

classed.2 <- krigged.ord.pred
classed.2$var1.pred[classed.2$var1.pred >= .66 & classed.2$var1.pred < 1] <- 3
classed.2$var1.pred[classed.2$var1.pred >= .33 & classed.2$var1.pred <.66] <- 2
classed.2$var1.pred[classed.2$var1.pred >= 0 & classed.2$var1.pred <.33] <- 1
writeGDAL(classed.2, fname=paste(DATA_PATH,
        "LULC_ordinary_krig_classed_2.tif", sep="/"), driver="GTiff")


# Check results with cross-validation
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
png(filename=paste(DATA_PATH, "LULC_ordinary_krig_bubble.png", sep="/"),
        width=8.33, height=5.33, units="in", res=300)
bubble(krigged.ord.cv5, "residual", main="Crossvalidation Residuals",
        maxsize=2, col=c("blue", "red"), sp.layout=list(i1, i2, i3))
dev.off()
