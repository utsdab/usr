#!/bin/bash

pwd=`pwd`
localdev='/Users/Shared/UTS_Dev/gitRepositories/utsdab/renderfarm/tractor/examples'
source='120988@localhost:'${localdev}/${1}

dest='mattg@138.25.37.155:/dabrender/mattg_testing_farm/upload/'

#cmd="rsync -avHS ${1} ${dest}"
cmd="scp  ${dest}/* ${localdev}"

echo ${cmd}

eval ${cmd}

