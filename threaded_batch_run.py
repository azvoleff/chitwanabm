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
# Contact Alex Zvoleff (azvoleff@mail.sdsu.edu) in the Department of Geography 
# at San Diego State University with any comments or questions. See the 
# README.txt file for contact information.

"""
Allows running a series of model runs (all of the same scenario) on a machine 
with more than one core.
"""

import sys
import time
import os

import argparse # Requires Python 2.7 or above
import signal
import threading
import subprocess
import logging
import socket

logger = logging.getLogger(__name__)

active_threads = []
def sighandler(num, frame):
    signal.signal(signal.SIGINT, sighandler)
    global sigint
    sigint = True
    logger.critical("System interrupt captured")
    for thread in list(active_threads):
        thread.kill()
    sys.exit()

sigint = False
signal.signal(signal.SIGINT, sighandler)

class ChitwanABMThread(threading.Thread):
    def __init__(self, thread_ID, runmodel_args):
        pool_sema.acquire()
        threading.Thread.__init__(self)
        self.threadID = thread_ID
        self.name = thread_ID
        self._runmodel_args = runmodel_args
        active_threads.append(self)

    def run(self):
        dev_null = open(os.devnull, 'w')
        command = rcParams['batchrun.python_path'] +  ' ' + rcParams['batchrun.runmodel_path'] +  ' ' + self._runmodel_args
        if '--log' not in command:
            command += ' --log=CRITICAL'
        self._modelrun = subprocess.Popen(command, cwd=sys.path[0], stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT)
        output, unused_err = self._modelrun.communicate()  # buffers the output
        retcode = self._modelrun.poll() 
        logger.info("Finished run %s (return code %s)"%(self.name, retcode))
        pool_sema.release()
        active_threads.remove(self)

    def kill(self):
        logger.warning("Killed run %s"%self.name)
        self._modelrun.terminate()

def main(argv=None):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    log_console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
            datefmt='%I:%M:%S%p')
    ch.setFormatter(log_console_formatter)
    root_logger.addHandler(ch)

    # Save args to pass on to runmodel
    if argv is None:
        argv = sys.argv
    runmodel_args = " ".join(argv[1:])

    parser = argparse.ArgumentParser(description='Run the ChitwanABM agent-based model (ABM).')
    parser.add_argument('--rc', dest="rc_file", metavar="RC_FILE", type=str, default=None,
            help='Path to a rc file to initialize a model run with custom parameters')
    args = parser.parse_args()

    from ChitwanABM import rc_params
    from PyABM.utility import email_logfile

    rc_params.load_default_params(os.path.dirname(os.path.realpath(__file__)))
    if not args.rc_file==None and not os.path.exists(args.rc_file):
        logger.critical('Custom rc file %s does not exist'%args.rc_file)
    rc_params.initialize(os.path.dirname(os.path.realpath(__file__)), args.rc_file)
    global rcParams
    rcParams = rc_params.get_params()

    scenario_path = os.path.join(str(rcParams['model.resultspath']), rcParams['scenario.name'])
    if not os.path.exists(scenario_path):
        try:
            os.mkdir(scenario_path)
        except OSError:
            logger.critical("Could not create scenario directory %s"%scenario_path)
            return 1

    batchrun_name = time.strftime("Batch_%Y%m%d-%H%M%S") + '_' + socket.gethostname()
    logfile = os.path.join(scenario_path, 'ChitwanABM_' + batchrun_name + '.log')
    logger.info("Logging to %s"%logfile)
    fh = logging.FileHandler(logfile)
    log_file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y/%m/%d %H:%M:%S')
    fh.setFormatter(log_file_formatter)
    root_logger.addHandler(fh)

    global pool_sema
    pool_sema = threading.BoundedSemaphore(value=(rcParams['batchrun.num_cores'] + 1))

    logger.info("Starting batch run %s, running '%s' scenario"%(batchrun_name, rcParams['scenario.name']))
    run_count = 1
    while run_count <= rcParams['batchrun.num_runs']:
        with pool_sema:
            new_thread = ChitwanABMThread(run_count, runmodel_args)
            logger.info("Starting run %s"%new_thread.name)
            new_thread.start()
            time.sleep(5)
            run_count += 1

    # Wait until all active threads have finished before emailing the log.
    for thread in list(active_threads):
        thread.join()

    if rcParams['email_log']:
        logger.info("Emailing log to %s"%rcParams['email_log.to'])
        subject = 'ChitwanABM Log - %s - %s'%(rcParams['scenario.name'], 
                batchrun_name)
        email_logfile(logfile, subject)
    logger.info("Finished batch run %s"%batchrun_name)

if __name__ == "__main__":
    sys.exit(main())
