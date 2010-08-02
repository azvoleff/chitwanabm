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

from ChitwanABM import rcParams
from ChitwanABM.modelloop import main_loop
from ChitwanABM.rcsetup import write_RC_file
from ChitwanABM.plotting import plot_pop_stats

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

def main(argv=None):
    if argv==None:
        argv = sys.argv

    try:
        rc_file = sys.argv[1]
        print "\nWARNING: using default rc params. Custom rc_file use is not yet implemented.\n"
    except IndexError:
        pass

    # The run_ID_number provides an ID number (built from the start time) to 
    # uniquely identify this model run.
    run_ID_number = time.strftime("%Y%m%d-%H%M%S")
    results_path = os.path.join(str(rcParams['model.resultspath']), run_ID_number)
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
    results = main_loop(world) # This line actually runs the model.
    end_time = time.localtime()
    end_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", end_time) 
    print """
*******************************************************************************
%s: finished model run number %s.
*******************************************************************************
"""%(end_time_string, run_ID_number)
    
    # Store the run ID in the results for later tracking purposes
    results.set_model_run_ID(run_ID_number)
    
    # Save the results
    print "Saving results...",
    results_file = os.path.join(results_path, "results.P")
    output = open(results_file, 'w')
    pickle.dump(results, output)
    output.close()

    # Save a plot of the results.
    plot_file = os.path.join(results_path, "plot.png")
    plot_pop_stats(results, plot_file)

    # Save the SHA-1 of the commit used to run the model, along with any diffs 
    # from the commit (the output of the git diff command). sys.path[0] gives 
    # the path of the currently running ChitwanABM code.
    git_diff_file = os.path.join(results_path, "git_diff.patch")
    commit_hash = save_git_diff(sys.path[0], git_diff_file)
    results_csv_file = os.path.join(results_path, "results.csv")
    save_results_csv(results, results_csv_file)

    # Calculate the number of seconds per month the model took to run (to 
    # simplify choosing what machine to do model runs on). This is equal to the 
    # length of results.get_timesteps() divided by the timestep size (in 
    # months).
    
    speed = (time.mktime(end_time) - time.mktime(start_time)) / (len(results.get_timesteps()) / rcParams['model.timestep'])

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

    print "done."

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

def save_results_csv(results, results_csv_file):
    out_file = open(results_csv_file, "w")
    csv_writer = csv.writer(out_file)
    csv_writer.writerows(results.get_results_array())
    out_file.close()

if __name__ == "__main__":
    sys.exit(main())
