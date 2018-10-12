#!/bin/env python
from config import *
import subprocess
from time import sleep
from random import randint
import sys
from os.path import isfile
from os import system

class Lsf:
    def __init__(self):
        self.outdir = OUTDIR
        self.account = ALLOC_ACCOUNT
        self.walltime = WALLTIME
        self.cpu = CPU
        self.memory = MEM
        self.queue = QUEUE
        self.jobs = []
        self.messages = None
        self.signals = None
        self.failed_bashes = None

    def config(self,outdir=OUTDIR,account=ALLOC_ACCOUNT,
               walltime=WALLTIME,cpu=CPU,memory=MEM,queue=QUEUE):
        self.outdir = outdir
        self.account = account
        self.walltime = walltime
        self.cpu = int(cpu)
        self.memory = int(memory)
        self.queue = queue # Change so that if the queue doesn't exist -- change the queue

    def set_job(self):
        fn = "%s/%s.sh" % (self.outdir,"".join([str(randint(0,9)) for i in range(8)]))
        while isfile(fn):
            fn = "%s/%s.sh" % (self.outdir,"".join([str(randint(0,9)) for i in range(8)]))
        return fn
    
    def combine_jobs(self,fn,add_fn):
        with open(fn,'a') as f1:
            if isfile(add_fn):
                f1.write("sh \"%s\"\n" % add_fn)
            else:
                f1.write("%s\n" % add_fn)

    def submit(self,command):
        commands = []
        if type(command) != type([]):
            commands = [command]
        else:
            commands = command
        for command in commands:
            name = "".join([str(randint(0,9)) for i in range(8)])
            # command = "submitjob %s -c %s -q %s -P %s -J %s -m %s -n 1 %s" % \
            #     (self.walltime,self.cpu,self.queue,self.account,name,self.memory,command)
            if isfile(command):
                submit_command = "bsub -W %s:00 -n %s -q %s -P %s -J %s -M %s -R \"span[ptile=%s]\" -e %s/%s.OU -o %s/%s.OU < %s" % \
                    (self.walltime,self.cpu,self.queue,self.account,name,self.memory*1000,self.cpu,self.outdir,name,self.outdir,name,command)
            else:
                submit_command = "bsub -W %s:00 -n %s -q %s -P %s -J %s -M %s -R \"span[ptile=%s]\" -e %s/%s.OU -o %s/%s.OU \"%s\"" % \
                    (self.walltime,self.cpu,self.queue,self.account,name,self.memory*1000,self.cpu,self.outdir,name,self.outdir,name,command)
            #print submit_command
            job = Job(name,command)
            job.submit(submit_command)
            self.jobs.append(job)
        
    def submit_file(self,lines,filename):
        fn = "%s/%s" % (self.outdir,filename)
        with open(fn,'w') as f:
            for line in lines:
                f.write("%s\n" % line)
        command="sh %s" % fn
        self.submit(command,name=filename)

    def write_ids(self,filename):
        with open(filename,'w') as fh:
            for job in self.jobs:
                jobfile = "%s/%s.OU" % (self.outdir,job.name)
                fh.write("%s\n" % jobfile)

    def wait(self):
        self.messages = set()
        self.signals = []
        self.failed_bashes = []
        for job in self.jobs:
            message, signal = job.done(self.outdir)
            self.messages.add(message)
            self.signals.append(signal)
            if signal == 2:
                self.failed_bashes.append(job.bashfn)
        while 0 in self.signals:
            sleep(SLEEPTIME)
            self.signals = []
            for job in self.jobs:
                message, signal = job.done(self.outdir)
                self.messages.add(message)
                self.signals.append(signal)
                if signal == 2:
                    self.failed_bashes.append(job.bashfn)

    def done(self,name=None):
        if name == None:
            return self.done_()
        else:
            for job in self.jobs:
                if job.name == name:
                    return job.done_(self.outdir)
        return False # False or error

    def done_(self):
        out = True
        for job in self.jobs:
            is_done = job.done_(self.outdir)
            if is_done == False:
                out = False
        return out

    def submit_config(self,command):
        # get current config
        # pass new config to config
        # submit
        # change to before configs
        pass

    def status(self):
        for message in self.messages:
            print message
        return (self.signals,self.failed_bashes)

class Job:
    def __init__(self,name,bashfn=None):
        self.name = name
        self.bashfn = bashfn
        self.command = None

    def submit(self,command):
        system(command)
        #result = subprocess.check_output(command, shell=False,stderr=subprocess.STDOUT)
        self.command = command

    def done_(self,outdir):
        jobfile = "%s/%s.OU" % (outdir,self.name)
        if isfile(jobfile):
            return True
        return False

    def done(self,outdir):
        # 0: not done, 1: done and passed, 2: done and failed
        outerr = "%s/%s.OU" % (outdir,self.name)
        message = None
        status = None
        if isfile(outerr):
            with open(outerr,'r') as f:
                for line in f:
                    line = line.rstrip()
                    if line.startswith('TERM_RUNLIMIT'):
                        message = 'JOB RAN OUT OF TIME, check %s' % outerr
                        status = 2
                    elif line.startswith('TERM_MEMLIMIT'):
                        message = 'JOB RAN OUT OF MEM, check %s' % outerr
                        status = 2
                    elif line.startswith('Exited with exit code'):
                        message = 'One of your jobs failed, check %s' % outerr
                        status = 2
                    elif line.startswith('Successfully completed'):
                        message = "Successfully completed"
                        status = 1
        else:
            message = "Not done"
            status = 0
        if message == None:
            sys.exit("Went through whole %s and did not find proper option...Exiting" % outerr)
        return (message,status)
