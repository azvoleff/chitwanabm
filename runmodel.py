#!/usr/bin/env python
# Copyright 2009 Alex Zvoleff
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

from ChitwanABM import rcParams
from ChitwanABM.modelloop import main_loop
from ChitwanABM.rcsetup import write_RC_file

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        rc_file = sys.argv[1]
        print "\nWARNING: using default rc params. Custom rc_file use is not yet implemented.\n"
    except IndexError:
        pass

    # The run_ID_number provides an ID number (built from the start time) to 
    # uniquely identify this model run.
    run_ID_number = time.strftime("%Y%m%d-%H%M%S")
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
            raise OSError("error creating scenario directory %s"%(scenario_path))
    try:
        os.mkdir(results_path)
    except OSError:
        raise OSError("error creating results directory %s"%(results_path))
    
    # Load a pickled World for use in the model.
    stored_init_data_file = rcParams['input.init_data_file']
    file = open(stored_init_data_file , "r")
    try:
        world = pickle.load(file)
    except IOError:
        raise IOError('error loading world data from  %s'%stored_init_data_file)

    # Run the model loop
    start_time = time.localtime()
    start_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", start_time)
    print """
*******************************************************************************
%s: started model run number %s.
*******************************************************************************
"""%(start_time_string, run_ID_number)
    pop_results, LULC_results, time_strings = main_loop(world, results_path) # This line actually runs the model.
    end_time = time.localtime()
    end_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", end_time) 
    print """
*******************************************************************************
%s: finished model run number %s.
*******************************************************************************
"""%(end_time_string, run_ID_number)
    
    # Save the results
    print "Saving results..."
    pop_data_file = os.path.join(results_path, "pop_results.P")
    output = open(pop_data_file, 'w')
    pickle.dump(pop_results, output)
    output.close()

    # Save the SHA-1 of the commit used to run the model, along with any diffs 
    # from the commit (the output of the git diff command). sys.path[0] gives 
    # the path of the currently running ChitwanABM code.
    git_diff_file = os.path.join(results_path, "git_diff.patch")
    commit_hash = save_git_diff(sys.path[0], git_diff_file)

    pop_results = reformat_pop_results(pop_results)
    pop_results_csv_file = os.path.join(results_path, "pop_results.csv")
    write_results_csv(pop_results, pop_results_csv_file, "neighid")

    LULC_csv_file = os.path.join(results_path, "LULC_results.csv")
    write_results_csv(LULC_results, LULC_csv_file, "neighid")

    time_csv_file = os.path.join(results_path, "time.csv")
    write_time_csv(time_strings, time_csv_file)
    
    if rcParams['model.make_plots']:
        print "Plotting results..."
        # Make plots of the LULC and population results
        dev_null = open(os.devnull, 'w')
        subprocess.check_call(['Rscript', 'plot_LULC.R', results_path],
                cwd=sys.path[0], stdout=dev_null, stderr=dev_null)
        subprocess.check_call(['Rscript', 'plot_pop.R', results_path],
                cwd=sys.path[0], stdout=dev_null, stderr=dev_null)
        if rcParams['save_psn_data']:
            subprocess.check_call(['Rscript', 'plot_psns_data.R', results_path],
                    cwd=sys.path[0], stdout=dev_null, stderr=dev_null)
        dev_null.close()

    # Calculate the number of seconds per month the model took to run (to 
    # simplify choosing what machine to do model runs on). This is equal to the 
    # length of time_strings divided by the timestep size (in months).
    speed = (time.mktime(end_time) - time.mktime(start_time)) / (len(time_strings['timestep']) / rcParams['model.timestep'])

    # Get machine hostname to print it in the results file
    hostname = socket.gethostname()
    
    # After running model, save rcParams to a file, along with the SHA-1 of the 
    # code version used to run it, and the start and finish times of the model 
    # run. Save this file in the same folder as the model output.
    run_RC_file = os.path.join(results_path, "ChitwanABMrc")
    RC_file_header = """# This file contains the parameters used for a ChitwanABM model run.
# Model run ID:\t%s
# Machine name:\t%s
# Start time:\t%s
# End time:\t\t%s
# Run speed:\t%.4f
# Code version:\t%s"""%(run_ID_number, hostname, start_time_string, end_time_string, speed, commit_hash)
    write_RC_file(run_RC_file, RC_file_header, rcParams)

    print "\nFinished at", time.strftime("%m/%d/%Y %I:%M:%S %p") + "."

def save_git_diff(code_path, git_diff_file):
    # First get commit hash from git show
    temp_file = tempfile.NamedTemporaryFile()
    try:
        subprocess.check_call(['git', 'show','--pretty=format:%H'], stdout=temp_file, cwd=code_path)
    except:
        print "Error running git. Skipping git-diff patch output."
        return "ERROR_RUNNING_GIT"
    temp_file = open(temp_file.name, "r")
    commit_hash = temp_file.readline().strip('\n')
    temp_file.close()

    # Now write output of git diff to a file.
    try:
        out_file = open(git_diff_file, "w")
    except IOError:
        raise IOError("error writing to git diff output file: %s"%(git_diff_file))
    subprocess.check_call(['git', 'diff'], stdout=out_file, cwd=code_path)
    out_file.close()
    return commit_hash

def reformat_pop_results(pop_results):
    """
    For convenience and speed while running the model, the population results 
    are stored in a dictionary keyed as [timestep][variable][neighborhoodid] = 
    value. The write_results_csv function (written to export them in a 
    conveient format for input into R) needs them to be keyed as 
    [timestep][neighborhoodid][variable] = value. This function will reformat 
    the pop_results to make them compatible with the write_results_csv 
    function.
    """
    pop_results_fixed = {}
    for timestep in pop_results.keys():
        pop_results_fixed[timestep] = {}
        for variable in pop_results[timestep].keys():
            for ID in pop_results[timestep][variable]:
                if not pop_results_fixed[timestep].has_key(ID):
                    pop_results_fixed[timestep][ID] = {}
                pop_results_fixed[timestep][ID][variable] = pop_results[timestep][variable][ID]
    return pop_results_fixed

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
        # Subtract 1 as Python has zero indexing but the model uses 1 to 
        # denote the first timestep.
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
                        row.append(np.NaN)
        csv_writer.writerow(row)
    out_file.close()

if __name__ == "__main__":
    sys.exit(main())
