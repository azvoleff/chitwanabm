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
import time
import pickle

from chitwanABM import rcParams

modelRunStartTime = time.time()    

if rcParams['model.use_psyco'] == True:
    import psyco
    psyco.full()

def main():
    # Initialize
    
    # Run the modellooop
    
    # Save the results

    # After running model, save rcParams to a file, along with the SHA-1 of the 
    # code version used to run it, and the start and finish times of the model 
    # run. Save this file in the same folder as the model output.

def elapsedTime(startTime):
    elapsed = int(time.time() - startTime)
    hours = elapsed / 3600
    minutes = (elapsed - hours * 3600) / 60
    seconds = elapsed - hours * 3600 - minutes * 60
    return "%ih %im %is" %(hours, minutes, seconds)

if __name__ == "__main__":
    sys.exit(main())
