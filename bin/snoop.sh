#!/bin/bash

h=`hostname | cut -d'.' -f1 `
ip=`ifconfig|grep 138.25`
u=$USER
i=`id`
g=`groups`
m=`umask`
t=`date "+%Y-%m-%d-%H-%M-%S"`
d=`date "+%Y-%m-%d"`

reportpath="/dabrender/usr/snoop/farmreports"
temppath="/dabrender/usr/snoop/tmp/tmp_$d"

case ${OSTYPE:0:5} in
linux)
    rfile="$reportpath/farmreport_$d"
    tfile="$temppath/tempfile_$h" 
    tdir="$temppath/tempdir_$h" 
;;
darwi)
    rfile="/Volumes/$reportpath/farmreport_$d"
    tfile="/Volumes/$temppath/tempfile_$h" 
    tdir="/Volumes/$temppath/tempdir_$h" 
;;
*)
    exit 1
;;
esac



if [ -e $tdir ]
then
	rm -rf $tdir
	echo "removed dir $tdir"
fi

mkdir -p $tdir
echo "made dir $tdir"

echo ">>>>"`ls -l $tdir/.. | grep $h`

if [ -e $tfile ]
then
	rm -f $tfile
	echo "removed file $tfile"
fi
touch $tfile
echo "made file $tfile"

echo ">>>>"`ls -l $tdir/.. | grep $h`
echo ">>>>>> The time is:"`date`

if [ -e $rfile ]
then
    echo "report file exists"
else
    echo "make report file $rfile"
    touch $rfile
fi


echo $tfile
echo $tdir
echo $rfile


echo "________________ $h $d _______________________" 	>> $rfile
echo "$h,$ip, _hostname     ,$h" 			>> $rfile
echo "$h,$ip, _ipaddress    ,$ip" 			>> $rfile
echo "$h,$ip, _user         ,$u" 			>> $rfile
echo "$h,$ip, _umask        ,$m" 			>> $rfile
echo "$h,$ip, _file         ,`ls -l $tfile`" 		>> $rfile
echo "$h,$ip, _dir          ,`ls -l $tdir/..|grep $h`" 	        >> $rfile
echo "$h,$ip, _id           ,$i" 			>> $rfile
echo "___________________________________________" 	>> $rfile
echo "" 						>> $rfile

tail $rfile
