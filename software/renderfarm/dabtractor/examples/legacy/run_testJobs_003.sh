#!/bin/bash

#  test maya batch with maya* envkey
/opt/pixar/tractor-blade/tractor-spool.py --engine=tractor-engine:5600 \
 --envkey=maya2014 --title=MAYABATCH_MR_ITERATE --jobcwd=/scratch/work/tmp \
 /dabrender/mattg_testing_farm/TESTJOB_MAYABATCH_MR2
