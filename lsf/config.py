#!/bin/env python
import sys
from os import makedirs,environ
from os.path import exists

### USER DEFINED VARIABLES
SCRATCH_DIR="/sc/hydra/scratch"
WALLTIME = 24
CPU = 1
MEM = 4
QUEUE = "private"
SLEEPTIME = 30
ALLOC_ACCOUNT = None 

if not exists(SCRATCH_DIR):
    SCRATCH_DIR="/tmp"

OUTDIR="%s/%s/lsf" % (SCRATCH_DIR,environ.get('USER'))
if not exists(OUTDIR):
    makedirs(OUTDIR)

if ALLOC_ACCOUNT == None:
    ALLOC_ACCOUNT = environ.get('SJOB_DEFALLOC')

if ALLOC_ACCOUNT == None:
    sys.exit('Initiate default allocation with '
             'SJOB_DEFALLOC environment')


