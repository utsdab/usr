#!/usr/bin/env rmanpy

import os
import sys
import datetime
import platform
import shutil
import subprocess


euid = os.geteuid()
print "euid={}".format(euid)

login = os.getlogin()
print "login={}".format(login)

groups = os.getgroups()
print "groups={}".format(groups)

egid = os.getegid()
print "egid={}".format(egid)

envuser = os.getenv("USER")
print "envuser={}".format(envuser)

uname = os.uname()
print "uname={}".format(uname)

gid = os.getgid()
print "gid={}".format(gid)

umask = os.umask(0002)
print "umask={}".format(umask)

umask2 = os.system("umask")
print "umask2={}".format(umask2)

now = datetime.datetime.now().date()
rightnow = datetime.datetime.now()
print "now={}".format(now)

dabrender = os.getenv("DABRENDER")
print "dabrender={}".format(dabrender)

mac_ver = platform.mac_ver()
print "mac_ver={}".format(mac_ver)

system = platform.system()
print "system={}".format(system)


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)


dirty = "/var/tmp/snoop/"
ensure_dir("/var/tmp/snoop/")
hostname = os.path.splitext(uname[1])[0]

dabrendermount = ""
try:
    if platform.system() == "Darwin":
        dabrendermount = "/Volumes/dabrender"
    elif platform.system() == "Linux":
        dabrendermount = "/dabrender"
except Exception, error3:
    sys.exit("Cant work out mounts")
finally:
    print "dabrendermount={}".format(dabrendermount)

resultspath = os.path.join(dabrendermount, "usr/snoop/results/snoop_{}/".format(now))
print "resultspath={}".format(resultspath)

writefile = os.path.join(resultspath, "{}.txt".format(hostname))
print("Write {}".format(writefile))

try:
    ensure_dir(resultspath)
except Exception, err:
    sys.exit(err)

# dirty = resultspath
print "cccc", dirty

tdir = os.path.join(resultspath, "{}_tdir/".format(hostname))
ensure_dir(tdir)
print tdir

tfile = os.path.join(tdir, "{}_tfile.txt".format(hostname))
print tfile

with open(tfile, "w") as mytfile:
    mytfile.writelines("{}\n".format(hostname))
    mytfile.writelines("uname={}\n".format(uname))
    mytfile.writelines("rightnow={}\n".format(rightnow))
    mytfile.close()

batcmdf = "ls -l {}".format(tfile)
outf = subprocess.check_output(batcmdf, shell=True)

batcmdd = "ls -l {}".format(resultspath)
outd = subprocess.check_output(batcmdd, shell=True)

with open(writefile, "w") as myfile:
    myfile.writelines("{}\n".format(hostname))
    myfile.writelines("uname={}\n".format(uname))
    myfile.writelines("rightnow={}\n".format(rightnow))
    myfile.writelines("login={}\n".format(login))
    myfile.writelines("euid={}\n".format(euid))
    myfile.writelines("egid={}\n".format(egid))
    myfile.writelines("umask={}\n".format(umask))
    myfile.writelines("umask2={}\n".format(umask2))
    myfile.writelines("dabrender={}\n".format(dabrender))
    myfile.writelines("system={}\n".format(system))
    myfile.writelines("mac_ver={}\n".format(mac_ver))
    myfile.writelines("gid={}\n\n".format(gid))
    myfile.writelines("tdir={}\n".format(tdir))
    myfile.writelines("{}\n\n".format(outd))
    myfile.writelines("tfile={}\n".format(tfile))
    myfile.writelines("{}\n".format(outf))
    myfile.close()

shutil.rmtree(tdir)
