import sys
import time
import os

import threading
import subprocess

number_of_runs = 10
max_threads = 2

time_format = "%m/%d/%Y %I:%M:%S %p"

pool_sema = threading.BoundedSemaphore(value=(max_threads+1))

python_path = "C:/Python27/python.exe"
script_path = "C:/Users/azvoleff/Code/Python/ChitwanABM/runmodel.py"
class ChitwanABMThread(threading.Thread):
    def __init__(self, thread_ID):
        pool_sema.acquire()
        threading.Thread.__init__(self)
        self.threadID = thread_ID
        self.name = thread_ID
    def run(self):
        dev_null = open(os.devnull, 'w')
        subprocess.check_call([python_path, script_path, "--log=CRITICAL"], cwd=sys.path[0])
        dev_null.close()
        end_time = time.strftime(time_format, time.localtime())
        print "%s: Finished run %s"%(end_time, self.name)
        pool_sema.release()

run_count = 1
while run_count <= number_of_runs:
    with pool_sema:
        new_thread = ChitwanABMThread(run_count)
        start_time = time.strftime(time_format, time.localtime())
        print "%s: Starting run %s"%(start_time, new_thread.name)
        new_thread.start()
        time.sleep(5)
        run_count += 1
