#!/usr/bin/env python
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

import numpy as np

from chitwanABM import rcParams, initialize, modelloop
from chitwanABM.agents import Region

# Try to load a random state from the rcfile
if rcParams['model.RandomState'] != None:
    np.random.RandomState = rcParams['model.RandomState']
else:
    # Otherwise store the current RandomState for later reuse (for testing, 
    # etc.)
    RandomState = np.random.RandomState
    rcParams['model.RandomState'] = RandomState

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

def main():
    # Initialize
    region = Region()
    initialize.assemble_region(region)

    # Run the model loop
    results = modelloop.main_loop(region)
    
    # Save the results
    print "\nSaving results to text...",
    results_file = os.path.join(str(rcParams['model.resultspath']), "results.P")
    output = open(results_file, 'w')
    pickle.dump(results, output)
    output.close()
    print "done."

    # After running model, save rcParams to a file, along with the SHA-1 of the 
    # code version used to run it, and the start and finish times of the model 
    # run. Save this file in the same folder as the model output.
    saved_params_file = os.path.join(str(rcParams['model.resultspath']), "chitwanABMrc")

    # TODO: write a function that will save the output of "git show" so that 
    # the SHA-1 of the commit is saved, along with any diffs from the commit.  
    # This file can also contain the start/stop times of the model run.

if __name__ == "__main__":
    sys.exit(main())
