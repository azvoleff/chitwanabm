import sys
import time
import os

import threading
import subprocess

number_of_runs = 20
max_threads = 3

python_path = "C:/Python27/python.exe"
script_path = "C:/Users/azvoleff/Code/Python/ChitwanABM/runmodel.py"
class ChitwanABMThread(threading.Thread):
    def __init__(self, thread_ID):
        threading.name = thread_ID
        threading.Thread.__init__(self)
    def run(self):
        dev_null = open(os.devnull, 'w')
        subprocess.check_call([python_path, script_path, "--log=CRITICAL"], cwd=sys.path[0])
        dev_null.close()
        start_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime())
        print "***************RUN %s FINISHED***************"%self.name

run_count = 1
while threading.active_count() <= max_threads and run_count <= number_of_runs:
    new_thread = ChitwanABMThread(run_count)
    start_time_string = time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime())
    print "***************STARTING RUN %s***************"%(run_count)
    new_thread.start()
    time.sleep(5)
    run_count += 1
