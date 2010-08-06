#!/usr/bin/env Rscript
# Plots the pop.results data from a model run.
require(ggplot2)

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
DATA_PATH <- "~/Data/ChitwanABM_runs/batchtest"

directories <- list.files(DATA_PATH)
pop.results <- list()
n <- 1
for (directory in directories) {
    full_directory_path <- paste(DATA_PATH, directory, sep="/") 
    pop.results.new <- calc_NBH_pop(full_directory_path)
    runname <- paste("run", n, sep="")
    names(pop.results.new) <- paste(names(pop.results.new), runname, sep=".")
    if (n==1) pop.results <- pop.results.new 
    else  pop.results <- cbind(pop.results, pop.results.new)
    n <- n + 1
}

ens_results <- calc_ensemble_results(pop.results)

make_shaded_error_plot(ens_results)
ggsave(paste(DATA_PATH, "batch_pop_results.png", sep="/"), width=8.33, height=5.53, dpi=300)
