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
# Contact Alex Zvoleff (azvoleff@mail.sdsu.edu) in the Department of Geography 
# at San Diego State University with any comments or questions. See the 
# README.txt file for contact information.

"""
Wrapper to run a set of Chitwan ABM model runs: Reads in input parameters, then 
calls routines to initialize and run the model, and output model statistics.

NOTE: Borrows code from matplotlib, particularly for rcsetup functions.
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
import argparse # Requires Python 2.7 or above
import logging
import shutil
from pkg_resources import resource_filename

import numpy as np
import tables

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Log to a temporary file until the final output log file path can be 
# constructed using the results path given in rcParams:
temp_log_file = tempfile.NamedTemporaryFile(delete=False)
temp_log = logging.FileHandler(temp_log_file.name)
temp_log.setLevel(logging.DEBUG)
log_file_formatter = logging.Formatter('%(asctime)s %(name)s:%(lineno)d %(levelname)s %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')
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

def main():
    parser = argparse.ArgumentParser(description='Run the chitwanabm agent-based model (ABM).')
    parser.add_argument('--rc', dest="rc_file", metavar="RC_FILE", type=str, default=None,
            help='Path to a rc file to initialize a model run with custom parameters')
    parser.add_argument('--log', metavar="LEVEL", type=str, default="info", 
            help='The logging threshold for logging to the console')
    parser.add_argument('--logf', metavar="LEVEL", type=str, 
            default="debug", help='The logging threshold for logging to the log file')
    parser.add_argument('--tail', dest='tail', action='store_const', 
            const=True, default=False, help='Tail the logfile with the default tail application specified in the rc parameters')
    parser.add_argument('--output-path', dest='output_path', default=None,
            help='Path in which to store the model output (overrides any value set in the rc-file)')
    parser.add_argument('--run-id', dest='run_ID_number', default=None,
            help='Run ID number (automatically generated if it is not specified)')
    args = parser.parse_args()

    # Setup logging according to the desired levels
    ch_level = getattr(logging, args.log.upper(), None)
    if not isinstance(ch_level, int):
        logger.critical('Invalid log level: %s' %args.log)
    root_logger.handlers[1].setLevel(ch_level)
    fh_level = getattr(logging, args.logf.upper(), None)
    if not isinstance(fh_level, int):
        logger.critical('Invalid log level: %s' %args.logf)
    root_logger.handlers[0].setLevel(fh_level)

    # Wait to load rcParams until here as logging statements are often 
    # triggered when the rcParams are loaded.
    from chitwanabm import rc_params
    # Make sure the rc_params are setup before loading any other chitwanabm 
    # modules, so that they will all take the default params including any that 
    # might be specified in user_rc_file
    root_logger.handlers[0].setLevel(fh_level)
    rc_params.load_default_params('chitwanabm')
    if not args.rc_file==None and not os.path.exists(args.rc_file):
        logger.critical('Custom rc file %s does not exist'%args.rc_file)
    rc_params.initialize('chitwanabm', args.rc_file)
    global rcParams
    rcParams = rc_params.get_params()

    from chitwanabm.initialize import generate_world
    from chitwanabm.modelloop import main_loop

    from pyabm.file_io import write_single_band_raster
    from pyabm.utility import save_git_diff
    from pyabm import __version__ as pyabm_version
    from chitwanabm import __version__ as chitwanabm_version

    if args.output_path != None:
        scenario_path = os.path.join(args.output_path, rcParams['scenario.name'])
        if not os.path.exists(args.output_path):
            try:
                os.mkdir(args.output_path)
            except OSError:
                logger.critical("Could not create output folder %s"%scenario_path)
                return 1
    else:
        scenario_path = os.path.join(rcParams['model.resultspath'], rcParams['scenario.name'])
    if not os.path.exists(scenario_path):
        try:
            os.mkdir(scenario_path)
        except OSError:
            logger.critical("Could not create scenario directory %s"%scenario_path)
            return 1

    if args.run_ID_number == None:
        # Get machine hostname to print it in the results file and use in the 
        # run_ID_number.
        hostname = socket.gethostname()
        # The run_ID_number provides an ID number (built from the start time 
        # and machine name) to uniquely identify this model run.
        run_ID_number = time.strftime("%Y%m%d-%H%M%S") + '_' + hostname
        results_path = os.path.join(scenario_path, run_ID_number)
        try:
            os.mkdir(results_path)
        except OSError:
            logger.critical("Could not create results directory %s"%results_path)
            return 1
    else:
        run_ID_number = args.run_ID_number
        results_path = os.path.join(scenario_path, run_ID_number)
        try:
            os.mkdir(results_path)
        except OSError:
            logger.critical("Could not create results directory %s"%results_path)
            return 1
        
    # Setup a special logger to log demographic events while the model is 
    # running (births, migrations, deaths, marriages, etc.)
    person_event_log_file_path = os.path.join(results_path, "person_events.log")
    person_event_log_file = open(person_event_log_file_path, mode='w')
    person_event_log_header = ",".join(["time", "event",
                                        "pid", "hid", "nid", "rid", "gender", "age", 
                                        "ethnicity", "mother_id", "father_id", 
                                        "spouseid", "marrtime", "schooling", 
                                        "num_children", "alive", "is_away", 
                                        "is_initial_agent", "is_in_migrant",
                                        "mother_num_children",
                                        "mother_years_schooling", 
                                        "mother_work", 
                                        "father_years_schooling","father_work", 
                                        "parents_contracep"])
    person_event_log_file.write(person_event_log_header + '\n')
    person_event_log_file.close()
    person_event_fh = logging.FileHandler(os.path.join(results_path, "person_events.log"), mode='a')
    person_event_fh.setLevel(logging.INFO)
    person_event_fh.setFormatter(logging.Formatter('%(modeltime)s,%(message)s,%(personinfo)s'))

    # Setup a filter so the agent event log will contain only agent events.
    class PassEventFilter(logging.Filter):
        def filter(self, record):
            logger_name = getattr(record, 'name', None)
            return 'person_events' in logger_name
    person_event_fh.addFilter(PassEventFilter())

    person_event_logger = logging.getLogger('person_events')
    person_event_logger.addHandler(person_event_fh)

    # Now that we know the rcParams and log file path, write the temp_log 
    # stream to the log file in the proper output directory, and direct all 
    # further logging to append to that file.
    log_file_path = os.path.join(results_path, "chitwanabm.log")
    shutil.copyfile(temp_log_file.name, log_file_path)
    temp_log_file.close()
    root_logger.handlers.remove(temp_log)
    temp_log.close()
    os.unlink(temp_log_file.name)
    new_fh = logging.FileHandler(log_file_path, mode='a')
    new_fh.setLevel(fh_level)
    new_fh.setFormatter(log_file_formatter)
    root_logger.addHandler(new_fh)
    # Dont' log agent event records to the main or console loggers
    class DontPassEventFilter(logging.Filter):
        def filter(self, record):
            logger_name = getattr(record, 'name', None)
            return 'person_events' not in logger_name
    for handler in root_logger.handlers:
        handler.addFilter(DontPassEventFilter())

    if args.tail:
        try:
            subprocess.Popen([rcParams['path.tail_binary'], log_file_path], cwd=results_path)
        except:
            logger.warning('Error tailing model log file: %s'%sys.exc_info()[1])

    # TODO: Fix the loading of a pickled world. For now, force regenerating the 
    # world each model run.
    # if rcParams['model.reinitialize']:
    #     # Generate a new world (with new resampling, etc.)
    #     world = generate_world()
    #     if world == 1:
    #         logger.critical('Error initializing model world')
    #         return 1
    # else:
    #     # Load a pickled World for use in the model.
    #     input_data_file = rcParams['path.input_data_file']
    #     file = open(input_data_file, "r")
    #     try:
    #         world = pickle.load(file)
    #     except IOError:
    #         logger.critical('Error loading world data from  %s'%input_data_file)
    #         return 1
    
    # Generate a new world (with new resampling, etc.)
    world = generate_world()
    if world == 1:
        logger.critical('Error initializing model world')
        return 1

    # Run the model loop
    start_time = time.localtime()
    logger.info('Beginning model run %s'%run_ID_number)
    run_results, time_strings, run_results_new_format = main_loop(world, results_path) # This line actually runs the model.
    end_time = time.localtime()
    logger.info('Finished model run number %s'%run_ID_number)
    
    # Save the results to a pickled file
    if rcParams['save_pickled_end_results']:
        logger.info("Saving results")
        pop_data_file = os.path.join(results_path, "run_results.P")
        output = open(pop_data_file, 'w')
        pickle.dump(run_results, output)
        output.close()
    # Save the results to a CSV
    run_results = reformat_run_results(run_results)
    run_results_csv_file = os.path.join(results_path, "run_results.csv")
    write_results_csv(run_results, run_results_csv_file, "neighid")

    run_results_new_format_h5_file = os.path.join(results_path, "results.h5")
    results_to_h5(run_results_new_format, run_results_new_format_h5_file, run_ID_number)
    results_to_csv(run_results_new_format, results_path)


    # Write neighborhood LULC, pop, x, y coordinates, etc. for the last 
    # timestep.
    world.write_NBHs_to_csv("END", results_path)

    # Write out the world file and mask used to run the model. Update the 
    # rcparams to point to these files so they will be reused if this run is 
    # rerun.
    DEM_data_file = os.path.join(results_path, "chitwanabm_DEM.tif")
    array, gt, prj = world.get_DEM_data()
    write_single_band_raster(array, gt, prj, DEM_data_file)
    world_mask_data_file = os.path.join(results_path, "chitwanabm_world_mask.tif")
    array, gt, prj = world.get_world_mask_data()
    write_single_band_raster(array, gt, prj, world_mask_data_file)

    # Save the SHA-1 of the commit used to run the model, along with any diffs 
    # from the commit (the output of the git diff command). sys.path[0] gives 
    # the path of the currently running chitwanabm code.
    git_diff_file = os.path.join(results_path, "git_diff.patch")
    commit_hash = save_git_diff(sys.path[0], git_diff_file)

    time_csv_file = os.path.join(results_path, "time.csv")
    write_time_csv(time_strings, time_csv_file)
    
    if rcParams['model.make_plots']:
        logger.info("Plotting population results")
        Rscript_binary = rcParams['path.Rscript_binary']
        plot_pop_script = resource_filename(__name__, 'R/plot_pop.R')
        try:
            output = subprocess.check_output([Rscript_binary, plot_pop_script, 
                results_path], cwd=sys.path[0], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            logger.exception("Problem running plot_pop.R. R output: %s"%e.output)

        if rcParams['save_NBH_data']:
            logger.info("Plotting LULC results")
            plot_LULC_script = resource_filename(__name__, 'R/plot_LULC.R')
            try:
                output = subprocess.check_output([Rscript_binary, plot_LULC_script, 
                    results_path], cwd=sys.path[0], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError, e:
                logger.exception("Problem running plot_LULC.R. R output: %s"%e.output)

        if rcParams['save_psn_data']:
            logger.info("Plotting persons results")
            plot_psns_script = resource_filename(__name__, 
                    'R/plot_psns_data.R')
            try:
                output = subprocess.check_output([Rscript_binary, plot_psns_script, 
                    results_path], cwd=sys.path[0], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError, e:
                logger.exception("Problem running plot_psns_data.R. R output: %s"%e.output)

    # Calculate the number of seconds per month the model took to run (to 
    # simplify choosing what machine to do model runs on). This is equal to the 
    # length of time_strings divided by the timestep size (in months).
    speed = (time.mktime(end_time) - time.mktime(start_time)) / (len(time_strings['timestep']) / rcParams['model.timestep'])

    start_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", start_time)
    end_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", end_time) 
    # After running model, save rcParams to a file, along with the SHA-1 of the 
    # code version used to run it, and the start and finish times of the model 
    # run. Save this file in the same folder as the model output.
    run_RC_file = os.path.join(results_path, "chitwanabmrc")
    RC_file_header = """# This file contains the parameters used for a chitwanabm model run.
# Model run ID:\t\t%s
# Start time:\t\t%s
# End time:\t\t\t%s
# Run speed:\t\t%.4f
# Code SHA:\t\t\t%s
# Code version:\t\t%s
# PyABM version:\t%s"""%(run_ID_number, start_time_string, end_time_string, 
        speed, commit_hash, chitwanabm_version, pyabm_version)
    rc_params.write_RC_file(run_RC_file, RC_file_header)

    # Write a file that can be used to confirm the run completed successfully
    finished_file = open(os.path.join(results_path, "RUN_FINISHED_OK"), "w")
    finished_file.close()

    logger.info("Finished saving results for model run %s"%run_ID_number)

    return 0

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
                if not ID in run_results_fixed[timestep]:
                    run_results_fixed[timestep][ID] = {}
                run_results_fixed[timestep][ID][variable] = run_results[timestep][variable][ID]
    return run_results_fixed

def write_time_csv(time_strings, time_csv_file):
    """
    Write a CSV file for conversion of timestep number, float, etc. to actual 
    year and month (for plotting).
    """
    out_file = open(time_csv_file, "wb")
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

#TODO: this function is deprecated and should be removed when the new record 
# array data storage is completed.
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
    out_file = open(csv_file, "wb")
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
                if ID in results[timestep]:
                    if category in results[timestep][ID]:
                        row.append(results[timestep][ID][category])
                    else:
                        row.append(0)
        csv_writer.writerow(row)
    out_file.close()

def results_to_h5(results, hdf_filename, run_ID_number):
    "Saves a dictionary of numpy structured arrays to HDF5 using pytables"
    filters = tables.Filters(complevel=5, complib='zlib')
    f = tables.openFile(hdf_filename, mode="w", title='ChitwanABM')
    for key in results:
        f.createTable('/', key, results[key], filters=filters)
    f.createArray('/', 'run_ID', np.array(run_ID_number))
    f.close()
    return 1

def results_to_csv(results, output_folder):
    "Saves numpy structured arrays from dictionary to gzipped CSV files"
    for key in results:
        # First need to setup format strings
        header_str = []
        offsets = []
        fmt_str = []
        dt_dict = results[key].dtype.fields
        for dt in dt_dict:
            header_str.append(dt)
            offsets.append(dt_dict[dt][1])
            dt_str = str(dt_dict[dt][0])
            if 'int' in dt_str:
                fmt_str.append('%i')
            elif 'float' in dt_str:
                fmt_str.append('%.18e')
            elif 'S' in dt_str:
                fmt_str.append('%s')
            else:
                raise IOError('unhandled data type %s in numpy structured array'%dt_str)
        # The fields in the dt_dict may not be sorted in order of the offsets, 
        # so the output and format strings may not match the data as output by 
        # savetxt unless we sort the format strings and header. We can figure 
        # out the proper sort order by looking at the offsets, which we need to 
        # reorder so they are in ascending order.
        fmt_str_decorated = [(offset, fmt) for fmt, offset in zip(fmt_str, 
            offsets)]
        fmt_str_decorated.sort()
        fmt_str = [fmt for offset, fmt in fmt_str_decorated]
        header_str_decorated = [(offset, header) for header, offset in 
                zip(header_str, offsets)]
        header_str_decorated.sort()
        header_str = [header for offset, header in header_str_decorated]
        header_str = ','.join(header_str)
        np.savetxt(os.path.join(output_folder, key + '.gz'), results[key], 
                delimiter=',', fmt=fmt_str, header=header_str, comments='')
    return 1

if __name__ == "__main__":
    sys.exit(main())
