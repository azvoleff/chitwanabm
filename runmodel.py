#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

Wrapper to run a set of CV_ABM_NS model runs: Reads in input parameters, then 
calls routines to initialize and run the model, and output model statistics.

NOTE: Borrows code from matplotlib, particularly for rcsetup functions.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import os
import sys
import getopt
import pickle

import numpy as np

from chitwanABM import rcParams, initialize, modelloop
from chitwanABM.agents import Region

try:
    # Try to load a random state from the rcfile
    np.random.RandomState = rcParams['model.RandomState']
except KeyError:
    # Otherwise store the current RandomState for later reuse (for testing, 
    # etc.)
    RandomState = np.random.RandomState
    rcParams['model.RandomState'] = RandomState

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

def main():
    # Initialize


    # Run the model loop
    modelloop.main_loop(regions)
    
    # Save the results

    # After running model, save rcParams to a file, along with the SHA-1 of the 
    # code version used to run it, and the start and finish times of the model 
    # run. Save this file in the same folder as the model output.
    results_dir = rcParams['model.RandomState']

if __name__ == "__main__":
    sys.exit(main())
