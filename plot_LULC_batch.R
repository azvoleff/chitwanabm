#!/usr/bin/env Rscript
# Plots the LULC data from a model run.
require(ggplot2, quietly=TRUE)

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

directories <- list.files(DATA_PATH)
# Only match the model results folders - don't match any other folders or files 
# in the directory, as trying to read results from these other files/folders 
# would lead to an error.
directories <- directories[grep("[0-9]{8}-[0-9]{6}", directories)]

lulc <- list()
n <- 1
for (directory in directories) {
    full_directory_path <- paste(DATA_PATH, directory, sep="/") 
    lulc.new <- calc_NBH_LULC(full_directory_path)
    runname <- paste("run", n, sep="")
    names(lulc.new) <- paste(names(lulc.new), runname, sep=".")
    if (n==1) lulc <- lulc.new 
    else  lulc <- cbind(lulc, lulc.new)
    n <- n + 1
}

ens_results <- calc_ensemble_results(lulc)

make_shaded_error_plot(ens_results, "Mean Percentage of Neighborhood", "LULC Type")
ggsave(paste(DATA_PATH, "batch_LULC.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)
