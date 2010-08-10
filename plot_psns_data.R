#!/usr/bin/env Rscript
# Plots the individual person data from a model run.
require(epicalc)

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]

files <- list.files(DATA_PATH)
# Only match the model results folders - don't match any other folders or files 
# in the directory, as trying to read results from these other files/folders 
# would lead to an error.
files <- files[grep("^psns_time_[0-9]*.txt$", files)]
# Sort the files by timestep
files <- files[order(as.numeric(gsub("(^psns_time_)|(.txt$)", "", files)))]
pdf_file_path <- paste(DATA_PATH, "/psns_pop_pyramid.pdf", sep="") 
pdf(file=pdf_file_path)
for (psns_file in files) {
    timestep <- gsub("(^psns_time_)|(.txt$)", "",  psns_file)
    full_file_path <- paste(DATA_PATH, "/", psns_file, sep="") 
    psns_data <- read.csv(full_file_path)
    # Cover ages from months to years
    psns_data$age <- psns_data$age/12
    pyramid(psns_data$age, psns_data$gender, main=paste("Timestep", timestep, sep=" "))
}
dev.off()
