# cluster
I usually end up writing python code that requires submitting jobs into the cluster and waiting for those jobs to finish in order to continue. So I created this code `cluster` that does that. 

In order to use it, first download and install `cluster`.

```
git clone https://github.com/oscarlr/cluster
python setup.py install --user
```

Here's an example of using `cluster`

```
from lsf.lsf import Lsf

def submit_jobs(samples,cluster,walltime,core,mem,queue,wait=True):
    jobs = []
    for sample in samples:
        if sample.submit == False:
            continue
        jobs.append(sample.bash_script)
        sample.submit = False
    if len(jobs) == 0:
        return
    if not cluster:
        for job in jobs:
            os.system("sh %s" % job)
        return
    hpc = Lsf()
    for job in jobs:
        hpc.config(cpu=core,
                   walltime=walltime,
                   memory=mem,
                   queue=queue)
        hpc.submit("%s" % job)
    if wait:
        hpc.wait()
```

In `submit_jobs` I create a list and add to this list file paths that point to bash scripts. Then I create an instance of Lsf() and used the function config from the instance to configure the job parameters, and then pass the file path of the bash script to the submit function from the instance. After all the jobs are submitted I call the function wait to wait until all the jobs are done.
