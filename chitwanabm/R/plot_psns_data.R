#!/usr/bin/env Rscript
#
# Copyright 2008-2012 Alex Zvoleff
#
# This file is part of the chitwanabm agent-based model.
# 
# chitwanabm is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# chitwanabm is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# chitwanabm.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff in the Department of Geography at San Diego State 
# University with any comments or questions. See the README.txt file for 
# contact information.

###############################################################################
# Plots the individual person data from a model run.
###############################################################################

require(epicalc)
require(ggplot2, quietly=TRUE)

PLOT_WIDTH = 8.33
PLOT_HEIGHT = 5.53
# Customize the ggplot2 theme
theme_set(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=1))

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

files <- list.files(DATA_PATH)
# Only match the model results folders - don't match any other folders or files 
# in the directory, as trying to read results from these other files/folders 
# would lead to an error.
files <- files[grep("^psns_time_[0-9]*.csv$", files)]
# Sort the files by timestep
files <- files[order(as.numeric(gsub("(^psns_time_)|(.csv$)", "", files)))]
pdf_file_path <- paste(DATA_PATH, "/psns_pop_pyramid.pdf", sep="") 
pdf(file=pdf_file_path)
hhsize <- c()
timesteps <-c()
for (psns_file in files) {
    timestep <- gsub("(^psns_time_)|(.csv$)", "",  psns_file)
    timesteps <- c(timesteps, timestep)
    full_file_path <- paste(DATA_PATH, "/", psns_file, sep="") 
    psns_data <- read.csv(full_file_path)
    # Cover ages from months to years
    psns_data$age <- psns_data$age/12
    pyramid(psns_data$age, psns_data$gender, main=paste("Timestep", timestep, sep=" "))
    hhsize <- c(hhsize, mean(table(psns_data$hid)))
}
dev.off()

time.values <- read.csv(paste(DATA_PATH, "time.csv", sep="/"))
time.Robj <- as.Date(paste(time.values$time_date, "15", sep=","),
        format="%m/%Y,%d")
time.values <- cbind(time.values, time.Robj=time.Robj)
time.Robj <- time.values$time.Robj[time.values$timestep %in% timesteps]

qplot(time.Robj, hhsize, geom="line", xlab="Year",
        ylab="Mean Household Size (number of persons)")
ggsave(paste(DATA_PATH, "hhsize.png", sep="/"), width=PLOT_WIDTH,
        height=PLOT_HEIGHT, dpi=300)
