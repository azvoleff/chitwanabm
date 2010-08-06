#!/usr/bin/env Rscript
# Plots the LULC data from a model run.
require(ggplot2)

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
ggsave(paste(DATA_PATH, "LULC.png", sep="/"), width=8.33, height=5.53,
        dpi=300)
