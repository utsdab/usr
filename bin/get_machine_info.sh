#!/bin/bash
echo "Getting machine info that is farm relevant"

h=`hostname | cut -d'.' -f1 `
ip=`/sbin/ifconfig |grep 138.25 | tr  -d ' '`
u=$USER
i=`id`
echo "--------------------------------"
echo "MACHINE: $h"
echo "IPADDRESS: $ip"
echo "USER: $u"
echo "ID: $i"
echo "/etc --------------------------------"
ls -lrt /etc | tail -10

echo "/etc --------------------------------"


echo "/etc --------------------------------"


echo "/etc --------------------------------"
