#!/usr/bin/env python
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
# See the README.rst file for author contact information.

"""
Wrapper to run R scripts processing scenario results.
"""

import os
import sys
import argparse
import subprocess
from pkg_resources import resource_filename

def main():
    parser = argparse.ArgumentParser(description='Run the chitwanabm agent-based model (ABM).')
    parser.add_argument(dest="directory", metavar="directory", type=str, default=None,
            help='Path to a folder of ChitwanABM run results.')
    parser.add_argument('--Rscript', dest="Rscript", metavar="Rscript_binary", type=str, default="/usr/bin/Rscript",
            help='Path to the Rscript binary.')
    args = parser.parse_args()

    if not os.path.exists(args.Rscript):
        sys.exit("Must provide a valid path to Rscript binary.")

    scenario_path = args.directory

    print "Running calculations for %s"%scenario_path
    batch_calc_script = resource_filename(__name__, 'R/batch_calculations.R')
    try:
        output = subprocess.check_output([args.Rscript, batch_calc_script, scenario_path], cwd=sys.path[0], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        print "Problem running calculations %s: %s"%(scenario_path, e.output)
        sys.exit(1)

    print "Running making plots for %s"%scenario_path
    batch_plot_script = resource_filename(__name__, 'R/batch_plots.R')
    try:
        output = subprocess.check_output([args.Rscript, batch_plot_script, scenario_path], cwd=sys.path[0], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        print "Problem making plots for %s: %s"%(scenario_path, e.output)
        sys.exit(1)

    finished_file = open(os.path.join(scenario_path, "SCENARIO_PROCESSED_OK"), "w")
    finished_file.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
