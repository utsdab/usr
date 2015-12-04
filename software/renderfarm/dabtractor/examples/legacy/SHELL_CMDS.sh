#!/bin/bash
#   test basic linux commands in envkey rms-*-maya-*
/opt/pixar/Tractor-2.0/bin/tractor-spool --engine=tractor-engine:5600  \
--envkey=rms-19.0-maya-2014 --title=SHELL_CMDS \
./SHELL_CMDS.alf
