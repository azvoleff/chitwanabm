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


def sighandler(num, frame):
  global sigint
  sigint = True

number_of_runs = 20
max_threads = 4

time_format = "%m/%d/%Y %I:%M:%S %p"

pool_sema = threading.BoundedSemaphore(value=(max_threads+1))

python_path = "C:/Python27_64bit/python.exe"
script_path = "C:/Users/azvoleff/Code/Python/ChitwanABM/runmodel.py"
#python_path = "/usr/bin/python"
#script_path = "/home/azvoleff/Code/Python/ChitwanABM/runmodel.py"
class ChitwanABMThread(threading.Thread):
    def __init__(self, thread_ID, runmodel_args):
        pool_sema.acquire()
        threading.Thread.__init__(self)
        self.threadID = thread_ID
        self.name = thread_ID
        self._runmodel_args = runmodel_args

    def run(self):
        dev_null = open(os.devnull, 'w')
        command = python_path +  ' ' + script_path +  ' ' + self._runmodel_args
        if '--log' not in command:
            command += ' --log=CRITICAL'
        self._modelrun = subprocess.Popen(command, cwd=sys.path[0], stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT)
        output, unused_err = self._modelrun.communicate()  # buffers the output
        retcode = self._modelrun.poll() 
        end_time = time.strftime(time_format, time.localtime())
        print "%s: Finished run %s (return code %s)"%(end_time, self.name, retcode)
        pool_sema.release()

    def kill(self):
        self._modelrun.terminate()
        print "%s: Killed run %s (return code %s)"%(end_time, self.name, retcode)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    runmodel_args = " ".join(argv[1:])

    sigint = False
    signal.signal(signal.SIGINT, sighandler)

    end_batch = False
    run_count = 1
    while run_count <= number_of_runs:
        with pool_sema:
            new_thread = ChitwanABMThread(run_count, runmodel_args)
            start_time = time.strftime(time_format, time.localtime())
            print "%s: Starting run %s"%(start_time, new_thread.name)
            try:
                new_thread.start()
            except (KeyboardInterrupt, SystemExit):
                new_thread.kill()
            if sigint:
                sys.exit()
            time.sleep(5)
            run_count += 1

if __name__ == "__main__":
    sys.exit(main())
