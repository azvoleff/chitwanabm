#!/usr/bin/python
"""
Part of Chitwan Valley agent-based model.

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

from chitwanABM import rcParams
from chitwanABM.modelloop import main_loop
from chitwanABM.initialize import assemble_world, load_world
from chitwanABM.rcsetup import write_RC_file
from chitwanABM.plotting import plot_pop_stats

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
    
    # Initialize
    stored_init_data = rcParams['input.init_data']
    if stored_init_data != "None":
        try:
            world = load_world(stored_init_data)
            print "Using saved world from %s..."%stored_init_data
        except IOError:
            print ('WARNING: error loading %s datafile'%stored_init_data)
            stored_init_data = "None"
    if stored_init_data == "None":
        print "Assembling world from pre-processed CVFS data..."
        world = assemble_world()

    # Run the model loop
    start_time = time.strftime("%m/%d/%Y %I:%M:%S %p")
    print """
*******************************************************************************
%s: started model run number %s.
*******************************************************************************
"""%(start_time, run_ID_number)
    results = main_loop(world) # This line actually runs the model.
    end_time = time.strftime("%m/%d/%Y %I:%M:%S %p") 
    print """
*******************************************************************************
%s: finished model run number %s.
*******************************************************************************
"""%(end_time, run_ID_number)
    
    # Store the run ID in the results for later tracking purposes
    results.set_model_run_ID(run_ID_number)
    
    # Save the results
    print "Saving results...",
    results_file = os.path.join(results_path, "results.P")
    output = open(results_file, 'w')
    pickle.dump(results, output)
    output.close()

    # Save a plot of the results.
    plot_file = os.path.join(results_path, "plot.pdf")
    plot_pop_stats(results, plot_file)

    # Save the SHA-1 of the commit used to run the model, along with any diffs 
    # from the commit (the output of the git diff command).
    git_diff_file = os.path.join(results_path, "git_diff.patch")
    commit_hash = save_git_diff("/home/azvoleff/Code/Python/chitwanABM", git_diff_file)

    # After running model, save rcParams to a file, along with the SHA-1 of the 
    # code version used to run it, and the start and finish times of the model 
    # run. Save this file in the same folder as the model output.
    run_RC_file = os.path.join(results_path, "chitwanABMrc")
    RC_file_header = """# This file contains the parameters used for a chitwanABM model run.
# Model run ID:\t%s
# Start time:\t%s
# End time:\t\t%s
# Code version:\t%s"""%(run_ID_number, start_time, end_time, commit_hash)
    write_RC_file(run_RC_file, RC_file_header, rcParams)

    print "done."

def save_git_diff(code_path, git_diff_file):
    # First get commit hash from git show
    temp_file = tempfile.NamedTemporaryFile()
    subprocess.check_call(['git', 'show','--pretty=format:%H'], stdout=temp_file, cwd=code_path)
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

if __name__ == "__main__":
    sys.exit(main())
