#!/usr/bin/env Rscript
# Plots the LULC data from a model run.
require(ggplot2)

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
DATA_PATH <- "~/Data/ChitwanABM_runs/batchtest"

directories <- list.files(DATA_PATH)
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

make_shaded_error_plot(ens_results)
ggsave(paste(DATA_PATH, "batch_LULC.png", sep="/"), width=8.33, height=5.53, dpi=300)
