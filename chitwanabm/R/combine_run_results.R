###############################################################################
# Combines the run_results.csv files from all the runs in a scenario into a 
# single dataframe, adds SCENARIO and RUN_ID fields, and saves the dataframe as 
# an Rdata file. This will take a little over 3GB of memory (for a set of forty 
# 50 year model runs).
###############################################################################

DATA_PATH <- commandArgs(trailingOnly=TRUE)[1]
if (is.na(DATA_PATH)) stop("Data path must be supplied")

SCENARIO <- commandArgs(trailingOnly=TRUE)[2]
if (is.na(DATA_PATH)) stop("Scenario name must be supplied")

run_dirs <-  list.dirs(file.path(DATA_PATH, SCENARIO), recursive=FALSE)

pb <- txtProgressBar(style=3)
for (run_dir_num in 1:length(run_dirs)) {
    setTxtProgressBar(pb, (run_dir_num - 1)/length(run_dirs))
    dir <- basename(run_dirs[run_dir_num])
    run_data <- read.csv(file.path(DATA_PATH, SCENARIO, dir, "run_results.csv"), 
                         stringsAsFactors=FALSE)
    run_data$SCENARIO <- SCENARIO
    run_data$RUN_ID <- paste(SCENARIO, dir, sep='_')

    if (run_dir_num == 1) {
        scenario_data <- run_data
    } else {
        scenario_data <- rbind(scenario_data, run_data)
    }

    rm(run_data)
    setTxtProgressBar(pb, (run_dir_num)/length(run_dirs))
}
close(pb)

save(scenario_data, file=file.path(DATA_PATH, SCENARIO, paste(SCENARIO, 'run_results.Rdata', sep='_')))
