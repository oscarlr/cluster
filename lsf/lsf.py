#!/bin/env python
import os
import sys
from config import *
import subprocess
from time import sleep
from random import randint


try:  # Forced testing
    from shutil import which
except ImportError:  # Forced testing
    # Versions prior to Python 3.3 don't have shutil.which
    def which(cmd, mode=os.F_OK | os.X_OK, path=None):
        """Given a command, mode, and a PATH string, return the path which
        conforms to the given mode on the PATH, or None if there is no such
        file.
        `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
        of os.environ.get("PATH"), or can be overridden with a custom search
        path.
        Note: This function was backported from the Python 3 source code.
        TAKEN FROM: https://github.com/cookiecutter/whichcraft
        Copyright (c) 2015-2016, Daniel Roy Greenfeld
        All rights reserved.

        """
        # Check that a given file can be accessed with the correct mode.
        # Additionally check that `file` is not a directory, as on Windows
        # directories pass the os.access check.

        def _access_check(fn, mode):
            return os.path.exists(fn) and os.access(fn, mode) and not os.path.isdir(fn)

        # If we're given a path with a directory part, look it up directly
        # rather than referring to PATH directories. This includes checking
        # relative to the current directory, e.g. ./script
        if os.path.dirname(cmd):
            if _access_check(cmd, mode):
                return cmd

            return None

        if path is None:
            path = os.environ.get("PATH", os.defpath)
        if not path:
            return None

        path = path.split(os.pathsep)

        if sys.platform == "win32":
            # The current directory takes precedence on Windows.
            if os.curdir not in path:
                path.insert(0, os.curdir)

            # PATHEXT is necessary to check on Windows.
            pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
            # See if the given file matches any of the expected path
            # extensions. This will allow us to short circuit when given
            # "python.exe". If it does match, only test that one, otherwise we
            # have to try others.
            if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
                files = [cmd]
            else:
                files = [cmd + ext for ext in pathext]
        else:
            # On other platforms you don't have things like PATHEXT to tell you
            # what file suffixes are executable, so just pass on cmd as-is.
            files = [cmd]

        seen = set()
        for dir in path:
            normdir = os.path.normcase(dir)
            if normdir not in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if _access_check(name, mode):
                        return name

        return None

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
        self.hpc_type = None
        if which('bsub') not None:
            self.hpc_type = "lsf"
        if which('srun') not None:
            self.hpc_type = "slurm"

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
        while os.isfile(fn):
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
                if self.hpc_type == "lsf":
                    submit_command = "bsub -W %s:00 -n %s -q %s -P %s -J %s -M %s -R \"span[ptile=%s]\" -e %s/%s.OU -o %s/%s.OU < %s" % \
                                     (self.walltime,self.cpu,self.queue,self.account,name,self.memory*1000,self.cpu,self.outdir,name,self.outdir,name,command)
                elif self.hpc_type == "slurm":
                    submit_command = "srun --time %s:00:00 -c %s -p %s -A %s -J %s --mem-per-cpu %sG -e %s/%s.OU -o %s/%s.OU < %s" % \
                                     (self.walltime,self.cpu,self.queue,self.account,name,self.memory,self.outdir,name,self.outdir,name,command)
            else:
                if self.hpc_type == "lsf":
                    submit_command = "bsub -W %s:00 -n %s -q %s -P %s -J %s -M %s -R \"span[ptile=%s]\" -e %s/%s.OU -o %s/%s.OU \"%s\"" % \
                                     (self.walltime,self.cpu,self.queue,self.account,name,self.memory*1000,self.cpu,self.outdir,name,self.outdir,name,command)
                elif self.hpc_type == "slurm":
                    submit_command = "srun --time %s:00:00 -c %s -p %s -A %s -J %s --mem-per-cpu %sG -e %s/%s.OU -o %s/%s.OU \"%s\"" % \
                                     (self.walltime,self.cpu,self.queue,self.account,name,self.memory,self.outdir,name,self.outdir,name,command)
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
        os.system(command)
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
