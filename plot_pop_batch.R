#!/usr/bin/env Rscript
# Plots the pop.results data from a model run.
require(ggplot2, quietly=TRUE)

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

directories <- list.files(DATA_PATH)
# Only match the model results folders - don't match any other folders or files 
# in the directory, as trying to read results from these other files/folders 
# would lead to an error.
directories <- directories[grep("[0-9]{8}-[0-9]{6}", directories)]

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
