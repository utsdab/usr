#!/bin/bash
#cut -d':' -f1 /etc/passwd
h=`hostname | cut -d'.' -f1 `
ip=`ifconfig|grep 138.25`
u=$USER
i=`id`
g=`groups`
m=`umask`
touch /tmp/xx_$h
mkdir -p /tmp/mm_$h
d=`date`


file="/Volumes/dabrender/work/matthewgidney/farmreport"


if [ -e $file ]
then
    echo "file exists"
else
    echo "make $file"
    touch $file
fi


echo "________________ $h $d _______________________" >> $file
echo "$h,$ip, _hostname     ,$h" >> $file
echo "$h,$ip, _ipaddress    ,$ip" >> $file
echo "$h,$ip, _user         ,$u" >> $file
echo "$h,$ip, _umask        ,$m" >> $file
echo "$h,$ip, _file ,`ls -l /tmp/|grep xx_$h`" >> $file
echo "$h,$ip, _dir ,`ls -l /tmp/|grep mm_$h`" >> $file
echo "$h,$ip, _id ,$i" >> $file
echo "___________________________________________" >> $file

tail $file

