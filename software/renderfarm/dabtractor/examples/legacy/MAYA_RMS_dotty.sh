#!/bin/bash

#  test maya batch with maya* envkey

cmd="/opt/pixar/Tractor-2.0/bin/tractor-spool"
env="rms-19.0-maya-2015"
title="MAYA_RMS_dotty"
file="/dabrender/mattg_testing_farm/upload/MAYA_RMS_dotty.alf"


command="${cmd} --engine=tractor-engine:5600 --envkey=${env} --title=${title} ${file}"
echo ${command}

eval ${command}
