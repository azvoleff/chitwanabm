#!/usr/bin/env Rscript
# Plots the LULC data from a model run.
require(ggplot2)

#MODEL_RUN_ID <- "20100803-161842"
#DATA_PATH <- paste("~/Data/ChitwanABM_runs", MODEL_RUN_ID, sep="/")
DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

theme_update(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=1))

# Make plots of LULC for a model run.
lulc <- read.csv(paste(DATA_PATH, "LULC_results.csv", sep="/"))
time.values <- read.csv(paste(DATA_PATH, "time.csv", sep="/"))
time.Robj <- as.Date(paste(time.values$time_date, "15", sep=","),
        format="%m/%Y,%d")
time.values <- cbind(time.values, time.Robj=time.Robj)

agveg.cols <- grep('^agveg.[0-9]*$', names(lulc))
nonagveg.cols <- grep('^nonagveg.[0-9]*$', names(lulc))
pubbldg.cols <- grep('^pubbldg.[0-9]*$', names(lulc))
privbldg.cols <- grep('^privbldg.[0-9]*$', names(lulc))
other.cols <- grep('^other.[0-9]*$', names(lulc))

# Calculate the total land area of each neighborhood
nbh.area <- apply(cbind(lulc$agveg.1, lulc$nonagveg.1, lulc$pubbldg.1,
        lulc$privbldg.1, lulc$other.1), 1, sum)

# And convert the LULC measurements from units of square meters to units that 
# are a percentage of total neighborhood area.
lulc.sd <- lulc/nbh.area

lulc.sd.mean <- data.frame(time.Robj=time.Robj,
        agveg=apply(lulc.sd[agveg.cols], 2, mean),
        nonagveg=apply(lulc.sd[nonagveg.cols], 2, mean),
        pubbldg=apply(lulc.sd[pubbldg.cols], 2, mean),
        privbldg=apply(lulc.sd[privbldg.cols], 2, mean),
        other=apply(lulc.sd[other.cols], 2, mean), row.names=NULL)
# Stack lulc.mean so it can easily be used with ggplot2 faceting
lulc.sd.mean <- stack(lulc.sd.mean)
lulc.sd.mean <- cbind(time.Robj=rep(time.Robj,5), lulc.sd.mean)
names(lulc.sd.mean)[2:3] <- c("area", "LULC_type")

qplot(time.Robj, area, geom="line", colour=LULC_type, xlab="Year",
        ylab="Mean Percentage of Neighborhood", data=lulc.sd.mean)
ggsave(paste(DATA_PATH, "LULC.png", sep="/"), width=8.33, height=5.53,
        dpi=300)
