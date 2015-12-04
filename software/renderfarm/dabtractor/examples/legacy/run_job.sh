#!/bin/bash

#  test maya batch with maya* envkey
#/opt/pixar/Tractor-2.0/bin/dabtractor-spool --engine=dabtractor-engine:5600  --envkey=maya2015 --title=BOWMAN --jobcwd=/scratch/work/tmp /dabrender/mattg_testing_farm/JOB_MAYA_MR_BOWMAN


cmd="/opt/pixar/Tractor-2.0/bin/tractor-spool"
cmd="/Applications/Pixar/Tractor-2.0/bin/tractor-spool"
env="maya2015"
title="TEST"
jobcwd="/scratch/work/tmp"
file="/dabrender/mattg_testing_farm/mattg/JOB_MAYA_MR_BOWMAN"

command="${cmd} --engine=tractor-engine:5600 --envkey=${env} --title=${title} --jobcwd=${jobcwd} ${file}"
echo ${command}

eval ${command}

