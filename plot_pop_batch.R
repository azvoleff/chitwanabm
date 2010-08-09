#!/usr/bin/env Rscript
# Plots the population data from a model run.
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

# First plot monthly event data
# Column 1 is times, so that column is always needed
events <- ens_results[c(1, grep("^(marr|births|deaths)", names(ens_results)))]
make_shaded_error_plot(events, "Number of Events", "Event Type")
ggsave(paste(DATA_PATH, "pop_events.png", sep="/"), width=8.33, height=5.53,
        dpi=300)

# Now plot total households and total marriages
num.hs.marr <- ens_results[c(1, grep("^(num_marr|num_hs)", names(ens_results)))]
make_shaded_error_plot(num.hs.marr, "Number", "Type")
ggsave(paste(DATA_PATH, "pop_num_hs_marr.png", sep="/"), width=8.33, height=5.53,
        dpi=300)

# Plot total population
update_geom_defaults("line", aes(size=1))
num_psn <- ens_results[c(1, grep("^(num_psn)", names(ens_results)))]
make_shaded_error_plot(num_psn, "Total Population", NA)
ggsave(paste(DATA_PATH, "pop_num_psn.png", sep="/"), width=8.33, height=5.53,
        dpi=300)

# Plot fw consumption in metric tons
fw_usage <- ens_results[c(1, grep("^(fw_usage)", names(ens_results)))]
fw_usage$fw_usage_kg.mean <- fw_usage$fw_usage_kg.mean/1000
fw_usage$fw_usage_kg.sd <- fw_usage$fw_usage_kg.sd/1000
make_shaded_error_plot(fw_usage, "Metric Tons of Fuelwood", NA)
ggsave(paste(DATA_PATH, "fw_usage.png", sep="/"), width=8.33, height=5.53,
        dpi=300)
