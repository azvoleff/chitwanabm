from __future__ import with_statement
from fabric.api import local, settings, abort, run, cd, env, put, task
from fabric.contrib.console import confirm
from fabric.tasks import Task

import os

rcfile_path = "C:/Users/azvoleff/ChitwanABM/rcfiles"

env.roledefs = {
    'manager': ['ubuntu@ec2-54-242-233-203.compute-1.amazonaws.com'],
    'worker':  ['ubuntu@ec2-54-242-72-224.compute-1.amazonaws.com']
}

env.key_filename = "C:/Users/azvoleff/Keys/azvoleff_ec2_keypair.pem"

@task
def clean_workers():
    run('rm /home/ubuntu/ChitwanABM/Tarballs/*')
    run('rm /home/ubuntu/ChitwanABM/rcfiles/*')
    run('rm /home/ubuntu/ChitwanABM/Runs/*')

@task
def update_workers():
    with cd('/home/ubuntu/Code/chitwanabm'):
        run('git pull')
    with cd('/home/ubuntu/Code/pyabm'):
        run('git pull')

@task
def start_workers():
    run('nohup /home/ubuntu/Code/chitwanabm/chitwanabm/misc/EC2_batch_run.sh &')

@task
def shutdown_workers():
    run('shutdown -h now')

class MyTask(Task):
    name = "deploy_rcfiles"
    def __init__(self, *args, **kwargs):
        super(MyTask, self).__init__(*args, **kwargs)
        num_workers = len(env.roledefs['worker'])
        rcfiles = [os.path.join(rcfile_path, rcfile) for rcfile in os.listdir(rcfile_path)]
        jobs_per_worker = [len(rcfiles) / num_workers] * num_workers
        for n in range(0, len(jobs_per_worker)):
            jobs_per_worker[n] += 1
            if sum(jobs_per_worker) == len(rcfiles): break
        self.worker_files = []
        index = 0
        for n in range(0, num_workers):
            self.worker_files.append(rcfiles[index:(index + jobs_per_worker[n])])
            index += num_per_worker[n]

    def run(self):
        for worker_file in self.worker_files[0]:
            put(worker_file, "/home/ubuntu/ChitwanABM/rcfiles")
            put("C:/Users/azvoleff/pyabmrc_EC2", "/home/ubuntu/pyabmrc")
        del self.worker_files[0]
instance = MyTask() 
