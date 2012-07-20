#!/usr/bin/env python
# Copyright 2008-2012 Alex Zvoleff
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

"""
Wrapper to run a set of Chitwan ABM model runs: Reads in input parameters, then 
calls routines to initialize and run the model, and output model statistics.

NOTE: Borrows code from matplotlib, particularly for rcsetup functions.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import os
import sys
import getopt
import time
import pickle
import tempfile
import subprocess
import socket
import csv
import numpy as np
import argparse # Requires Python 2.7 or above
import logging
import shutil

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Log to a temporary file until the final output log file path can be 
# constructed using the results path given in rcParams:
temp_log_file = tempfile.NamedTemporaryFile(delete=False)
temp_log = logging.FileHandler(temp_log_file.name)
temp_log.setLevel(logging.DEBUG)
log_file_formatter = logging.Formatter('%(asctime)s %(name)s:%(lineno)d %(levelname)s %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')
temp_log.setFormatter(log_file_formatter)
root_logger.addHandler(temp_log)
# Add a console logger as well - the level will be updated from the command 
# line parameters later as necessary.
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
log_console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
        datefmt='%I:%M:%S%p')
ch.setFormatter(log_console_formatter)
root_logger.addHandler(ch)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(description='Run the ChitwanABM agent-based model (ABM).')
    parser.add_argument('--rc', metavar="RC_FILE", type=str, default=None,
            help='Path to a rc file to initialize a model run with custom parameters')
    parser.add_argument('--log', metavar="LEVEL", type=str, default="info", 
            help='The logging threshold for logging to the console')
    parser.add_argument('--logf', metavar="LEVEL", type=str, 
            default="debug", help='The logging threshold for logging to the log file')
    args = parser.parse_args()

    # Setup logging according to the desired levels
    ch_level = getattr(logging, args.log.upper(), None)
    if not isinstance(ch_level, int):
        logger.critical('Invalid log level: %s' %args.log)
    root_logger.handlers[1].setLevel(ch_level)
    fh_level = getattr(logging, args.logf.upper(), None)
    if not isinstance(fh_level, int):
        logger.critical('Invalid log level: %s' %args.log_file)
    root_logger.handlers[0].setLevel(fh_level)

    if not(args.rc == None):
        logger.critical("An rc file path was passed as a command line parameter, but custom rc file use is not yet implemented.")
        return 1

    # Wait to load rcParams until here as logging statements are often 
    # triggered when the rcParams are loaded.
    global rcParams
    from ChitwanABM import rcParams
    from ChitwanABM.initialize import generate_world
    from ChitwanABM.modelloop import main_loop

    from PyABM.rcsetup import write_RC_file
    from PyABM.file_io import write_single_band_raster

    # Get machine hostname to print it in the results file and use in the 
    # run_ID_number.
    hostname = socket.gethostname()
    # The run_ID_number provides an ID number (built from the start time and 
    # machine name) to uniquely identify this model run.
    run_ID_number = time.strftime("%Y%m%d-%H%M%S") + '_' + hostname
    # First strip any trailing backslash from the model.resultspath value from 
    # rcparams, so that os.path.join-ing it to the scenario.name does not lead 
    # to having two backslashes in a row.
    model_results_path_root = str.strip(rcParams['model.resultspath'], "/\\")
    scenario_path = os.path.join(str(rcParams['model.resultspath']), rcParams['scenario.name'])
    results_path = os.path.join(scenario_path, run_ID_number)
    if not os.path.exists(scenario_path):
        try:
            os.mkdir(scenario_path)
        except OSError:
            logger.critical("Could not create scenario directory %s"%scenario_path)
            return 1
    try:
        os.mkdir(results_path)
    except OSError:
        logger.critical("Could not create results directory %s"%results_path)
        return 1
    
    # Now that we know the rcParams and log file path, write the temp_log 
    # stream to the log file in the proper output directory, and direct all 
    # further logging to append to that file.
    log_file_path = os.path.join(results_path, "ChitwanABM.log")
    shutil.copyfile(temp_log_file.name, log_file_path)
    temp_log_file.close()
    root_logger.handlers.remove(temp_log)
    temp_log.close()
    os.unlink(temp_log_file.name)
    fh = logging.FileHandler(log_file_path, mode='a')
    fh.setLevel(fh_level)
    fh.setFormatter(log_file_formatter)
    root_logger.addHandler(fh)

    if rcParams['model.reinitialize']:
        # Generate a new world (with new resampling, etc.)
        world = generate_world()
        if world == 1:
            logger.critical('Error initializing model world')
            return 1
    else:
        # Load a pickled World for use in the model.
        input_data_file = rcParams['path.input_data_file']
        file = open(input_data_file, "r")
        try:
            world = pickle.load(file)
        except IOError:
            logger.critical('Error loading world data from  %s'%input_data_file)
            return 1

    # Run the model loop
    start_time = time.localtime()
    logger.info('Beginning model run %s'%run_ID_number)
    run_results, time_strings = main_loop(world, results_path) # This line actually runs the model.
    end_time = time.localtime()
    logger.info('Finished model run number %s'%run_ID_number)
    
    # Save the results
    logger.info("Saving results")
    pop_data_file = os.path.join(results_path, "run_results.P")
    output = open(pop_data_file, 'w')
    pickle.dump(run_results, output)
    output.close()

    # Write neighborhood LULC, pop, x, y coordinates, etc. for the last 
    # timestep.
    world.write_NBHs_to_csv("END", results_path)

    # Write out the world file and mask used to run the model. Update the 
    # rcparams to point to these files so they will be reused if this run is 
    # rerun.
    DEM_data_file = os.path.join(results_path, "ChitwanABM_DEM.tif")
    array, gt, prj = world.get_DEM_data()
    write_single_band_raster(array, gt, prj, DEM_data_file)
    world_mask_data_file = os.path.join(results_path, "ChitwanABM_world_mask.tif")
    array, gt, prj = world.get_world_mask_data()
    write_single_band_raster(array, gt, prj, world_mask_data_file)

    # Save the SHA-1 of the commit used to run the model, along with any diffs 
    # from the commit (the output of the git diff command). sys.path[0] gives 
    # the path of the currently running ChitwanABM code.
    git_diff_file = os.path.join(results_path, "git_diff.patch")
    commit_hash = save_git_diff(sys.path[0], git_diff_file)

    run_results = reformat_run_results(run_results)
    run_results_csv_file = os.path.join(results_path, "run_results.csv")
    write_results_csv(run_results, run_results_csv_file, "neighid")

    time_csv_file = os.path.join(results_path, "time.csv")
    write_time_csv(time_strings, time_csv_file)
    
    if rcParams['model.make_plots']:
        logger.info("Plotting population results")
        Rscript_binary = rcParams['path.Rscript_binary']
        dev_null = open(os.devnull, 'w')
        try:
            subprocess.check_call([Rscript_binary, 'plot_pop.R', results_path],
                    cwd=sys.path[0], stdout=dev_null, stderr=dev_null)
        except:
            logger.exception("Problem running plot_pop.R")
        dev_null.close()

        if rcParams['save_NBH_data']:
            logger.info("Plotting LULC results")
            # Make plots of the LULC and population results
            dev_null = open(os.devnull, 'w')
            try:
                subprocess.check_call([Rscript_binary, 'plot_LULC.R', results_path],
                        cwd=sys.path[0], stdout=dev_null, stderr=dev_null)
            except:
                logger.exception("Problem running plot_LULC.R")
            dev_null.close()

        if rcParams['save_psn_data']:
            logger.info("Plotting persons results")
            dev_null = open(os.devnull, 'w')
            try:
                subprocess.check_call([Rscript_binary, 'plot_psns_data.R', results_path],
                        cwd=sys.path[0], stdout=dev_null, stderr=dev_null)
            except:
                logger.exception("Problem running plot_psns_data.R")
            dev_null.close()

    # Calculate the number of seconds per month the model took to run (to 
    # simplify choosing what machine to do model runs on). This is equal to the 
    # length of time_strings divided by the timestep size (in months).
    speed = (time.mktime(end_time) - time.mktime(start_time)) / (len(time_strings['timestep']) / rcParams['model.timestep'])

    start_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", start_time)
    end_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", end_time) 
    # After running model, save rcParams to a file, along with the SHA-1 of the 
    # code version used to run it, and the start and finish times of the model 
    # run. Save this file in the same folder as the model output.
    run_RC_file = os.path.join(results_path, "ChitwanABMrc")
    RC_file_header = """# This file contains the parameters used for a ChitwanABM model run.
# Model run ID:\t%s
# Start time:\t%s
# End time:\t\t%s
# Run speed:\t%.4f
# Code version:\t%s"""%(run_ID_number, start_time_string, end_time_string, 
        speed, commit_hash)
    write_RC_file(run_RC_file, RC_file_header, rcParams)

    logger.info("Finished saving results for model run %s"%run_ID_number)

    return 0

def save_git_diff(code_path, git_diff_file):
    # First get commit hash from git show
    temp_file_fd, temp_file_path = tempfile.mkstemp()
    try:
        git_binary = rcParams['path.git_binary']
        subprocess.check_call([git_binary, 'show','--pretty=format:%H'], stdout=temp_file_fd, cwd=code_path)
    except:
        logger.exception("Problem running git. Skipping git-diff patch output.")
        return 1
    os.close(temp_file_fd)
    temp_file = open(temp_file_path, 'r')
    commit_hash = temp_file.readline().strip('\n')
    temp_file.close()
    os.remove(temp_file_path)

    # Now write output of git diff to a file.
    try:
        out_file = open(git_diff_file, "w")
        git_binary = rcParams['path.git_binary']
        subprocess.check_call([git_binary, 'diff'], stdout=out_file, cwd=code_path)
        out_file.close()
    except IOError:
        logger.exception("Problem writing to git diff output file %s"%git_diff_file)
    return commit_hash

def reformat_run_results(run_results):
    """
    For convenience and speed while running the model, the population results 
    are stored in a dictionary keyed as [timestep][variable][neighborhoodid] = 
    value. The write_results_csv function (written to export them in a 
    conveient format for input into R) needs them to be keyed as 
    [timestep][neighborhoodid][variable] = value. This function will reformat 
    the run_results to make them compatible with the write_results_csv 
    function.
    """
    run_results_fixed = {}
    for timestep in run_results.keys():
        run_results_fixed[timestep] = {}
        for variable in run_results[timestep].keys():
            for ID in run_results[timestep][variable]:
                if not run_results_fixed[timestep].has_key(ID):
                    run_results_fixed[timestep][ID] = {}
                run_results_fixed[timestep][ID][variable] = run_results[timestep][variable][ID]
    return run_results_fixed

def write_time_csv(time_strings, time_csv_file):
    """
    Write a CSV file for conversion of timestep number, float, etc. to actual 
    year and month (for plotting).
    """
    out_file = open(time_csv_file, "w")
    csv_writer = csv.writer(out_file)
    col_headers = sorted(time_strings.keys())
    csv_writer.writerow(col_headers)
    columns = []
    for col_header in col_headers:
        # Subtract 1 as Python has zero indexing but the model uses 1 to denote 
        # the first timestep.
        if columns == []:
            columns = np.array((time_strings[col_header]))
        else:
            columns = np.vstack((columns, time_strings[col_header]))
    columns = np.transpose(columns)
    csv_writer.writerows(columns)
    out_file.close()

def write_results_csv(results, csv_file, ID_col_name):
    "Write to CSV the saved model run data."
    # The data is stored in a dictionary keyed by timestep, then keyed by ID, 
    # then keyed by category. Write it to CSV where each row represents a 
    # single agent (neighborhood, person, etc.), and each col a single variable 
    # (from a single timestep).
    timesteps = sorted(results.keys())
 
    # The IDs will uniquely identify each row of the final matrix.
    IDs = []
    for timestep in timesteps:
        IDs.extend(results[timestep].keys())
    IDs = sorted(np.unique(IDs))

    # Now figure out the categories to use them as row_headers
    categories = []
    for timestep in timesteps:
        for ID in results[timestep].keys():
            categories.extend(results[timestep][ID].keys())
    categories = sorted(np.unique(categories))

    # The dataframe will end up (in R) having 1 column for agent ID, and 
    # timesteps * categories additional columns for the data.
    out_file = open(csv_file, "w")
    csv_writer = csv.writer(out_file)
    var_names = [ID_col_name]
    for category in categories:
        for timestep in timesteps:
            var_name = category + "." + str(timestep)
            var_names.append(var_name)
    csv_writer.writerow(var_names)

    for ID in IDs:
        row = [ID]
        for category in categories:
            for timestep in timesteps:
                if results[timestep].has_key(ID):
                    if results[timestep][ID].has_key(category):
                        row.append(results[timestep][ID][category])
                    else:
                        row.append(0)
        csv_writer.writerow(row)
    out_file.close()

if __name__ == "__main__":
    sys.exit(main())
