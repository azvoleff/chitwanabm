#!/usr/bin/env Rscript
#
# Copyright 2011 Alex Zvoleff
#
# This file is part of the ChitwanABM agent-based model.
# 
# ChitwanABM is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# ChitwanABM is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# ChitwanABM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff in the Department of Geography at San Diego State 
# University with any comments or questions. See the README.txt file for 
# contact information.

###############################################################################
# Plots the population data from a model run.
###############################################################################

require(ggplot2, quietly=TRUE)
PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53
DPI = 300
theme_update(theme_grey(base_size=18))

source("calc_NBH_stats.R")

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
DATA_PATH <- "R:/Data/Nepal/ChitwanABM_runs/USIALE2012_nofeedback"

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
save(ens_results, file=paste(DATA_PATH, "ens_results_pop.Rdata", sep="/"))
write.csv(ens_results, file=paste(DATA_PATH, "ens_results_pop.csv", sep="/"))

# First plot monthly event data
# Column 1 is times, so that column is always needed
events <- ens_results[c(1, grep("^(marr|births|deaths)", names(ens_results)))]
make_shaded_error_plot(events, "Number of Events", "Event Type")
ggsave(paste(DATA_PATH, "pop_events.png", sep="/"), width=PLOT_WIDTH, height=PLOT_HEIGHT,
        dpi=DPI)

# Now plot total households and total marriages
num.hs.marr <- ens_results[c(1, grep("^(num_marr|num_hs)", names(ens_results)))]
make_shaded_error_plot(num.hs.marr, "Number", "Type")
ggsave(paste(DATA_PATH, "pop_num_hs_marr.png", sep="/"), width=PLOT_WIDTH, height=PLOT_HEIGHT,
        dpi=DPI)

# Plot total population
num_psn <- ens_results[c(1, grep("^(num_psn)", names(ens_results)))]
make_shaded_error_plot(num_psn, "Total Population", NA)
ggsave(paste(DATA_PATH, "pop_num_psn.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)

# Plot fw consumption in metric tons
fw_usage <- ens_results[c(1, grep("^(fw_usage)", names(ens_results)))]
fw_usage$fw_usage_metrictons.mean <- fw_usage$fw_usage_kg.mean/1000
fw_usage$fw_usage_metrictons.sd <- fw_usage$fw_usage_kg.sd/1000
fw_usage <- fw_usage[!("kg" %in% names(fw_usage))]
make_shaded_error_plot(fw_usage, "Metric Tons of Fuelwood", NA)
ggsave(paste(DATA_PATH, "fw_usage.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)
write.csv(fw_usage, file=paste(DATA_PATH, "fw_usage_ens_results.csv", sep="/"))
