#!/usr/bin/env python
import sys
import time
import os

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
    def __init__(self, thread_ID):
        pool_sema.acquire()
        threading.Thread.__init__(self)
        self.threadID = thread_ID
        self.name = thread_ID

    def run(self):
        dev_null = open(os.devnull, 'w')
        self._modelrun = subprocess.Popen(python_path +  ' ' + script_path +  ' --log=CRITICAL',
                cwd=sys.path[0], stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT)
        output, unused_err = self._modelrun.communicate()  # buffers the output
        retcode = self._modelrun.poll() 
        end_time = time.strftime(time_format, time.localtime())
        print "%s: Finished run %s (return code %s)"%(end_time, self.name, retcode)
        pool_sema.release()

    def kill(self):
        self._modelrun.terminate()
        print "%s: Killed run %s (return code %s)"%(end_time, self.name, retcode)

def main():
    sigint = False
    signal.signal(signal.SIGINT, sighandler)

    end_batch = False
    run_count = 1
    while run_count <= number_of_runs:
        with pool_sema:
            new_thread = ChitwanABMThread(run_count)
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
