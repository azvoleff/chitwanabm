#!/usr/bin/env Rscript
#
# Copyright 2008-2013 Alex Zvoleff
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
# Used for debugging after a model run when person data output is enabled - 
# outputs the general trend in the predictors for the marriage and first birth 
# timing models to check for input errors, unit errors, etc.
###############################################################################

run_path <- commandArgs(trailingOnly=TRUE)[1]
if (is.na(run_path)) stop("Run path must be supplied")

person_data_files <- list.files(run_path, "^psns_time_")

timesteps <- as.numeric(gsub('(psns_time_)|(.csv)', '', person_data_files))

person_data_files <- person_data_files[order(timesteps)]
timesteps <- sort(timesteps)

times <- 1997+(timesteps / 12)
for (n in 1:length(person_data_files)) {
    person_data_file <- person_data_files[n]
    time <- times[n]
    data <- read.csv(paste(run_path, person_data_file, sep="/"))
    data <- data[data$age > 18 & data$age < 60, ]
    print(paste('time:', time, '| schl:', mean(data$schooling),
                '| moth num child:', mean(data$mother_num_children),
                '| moth yrs schl:', mean(data$mother_years_schooling),
                '| moth work:', mean(as.numeric(data$mother_work)),
                '| fath yrs schl:', mean(data$father_years_schooling),
                '| fath work:', mean(as.numeric(data$father_work)),
                '| par contr:', mean(as.numeric(data$parents_contracep))))
}
