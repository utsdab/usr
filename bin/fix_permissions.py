#!/usr/bin/env python
'''
#!/usr/bin/env rmanpy
command to be run as a farm job by pixar   or from command line
attempts to make sure group is owned by pixar user 8888
and is
rwxrwsr_x  for directories
rw_rw_r__  for files
user:pixar

The setuid bit is not ignored on OS X, how do you think a program like the sudo you mention would be able to work if not thanks to it being setuid root? What seems to be a restriction in OS X, and apparently is not documented, is that the setuid bit on an executable has an effect only if the executable is in a directory that is owned by root (and not open for writing by others), etc, up to the root directory.

'''

#TODO this is a working acript but doesnt work on the farm because of permissions
#TODO tried seting the suid and letting root own it but no luck - maybe a root trust thing.

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)

import os
import argparse
import stat

def dochmod(path):
    '''
    This is going to be octal stuff
    http://permissions-calculator.org

    0664 ---> rw_rw_r__
    0775 ---> rwxrwxr_x
    2775 ---> rwxrwxsr_x     setgid
    3775 ---> rwxrwxsr_xt    setgid and stickybit

    to call these as octal in chmod
    If you're wondering why that leading zero is important, it's because permissions are set as an octal integer,
    and Python automagically treats any integer with a leading zero as octal. So os.chmod("file", 484)
    (in decimal) would give the same result.

    The following flags can also be used in the mode argument of os.chmod():

    stat.S_ISUID Set UID bit.
    stat.S_ISGID Set-group-ID bit. This bit has several special uses. For a directory it indicates that BSD semantics is to be used for that directory: files created there inherit their group ID from the directory, not from the effective group ID of the creating process, and directories created there will also get the S_ISGID bit set. For a file that does not have the group execution bit (S_IXGRP) set, the set-group-ID bit indicates mandatory file/record locking (see also S_ENFMT).
    stat.S_ISVTX Sticky bit. When this bit is set on a directory it means that a file in that directory can be renamed or deleted only by the owner of the file, by the owner of the directory, or by a privileged process.
    stat.S_IRWXU Mask for file owner permissions.
    stat.S_IRUSR Owner has read permission.
    stat.S_IWUSR Owner has write permission.
    stat.S_IXUSR Owner has execute permission.
    stat.S_IRWXG Mask for group permissions.
    stat.S_IRGRP Group has read permission.
    stat.S_IWGRP Group has write permission.
    stat.S_IXGRP Group has execute permission.
    stat.S_IRWXO Mask for permissions for others (not in group).
    stat.S_IROTH Others have read permission.
    stat.S_IWOTH Others have write permission.
    stat.S_IXOTH Others have execute permission.
    stat.S_ENFMT System V file locking enforcement. This flag is shared with S_ISGID: file/record locking is enforced on files that do not have the group execution bit (S_IXGRP) set.
    stat.S_IREAD Unix V7 synonym for S_IRUSR.
    stat.S_IWRITE Unix V7 synonym for S_IWUSR.
    stat.S_IEXEC Unix V7 synonym for S_IXUSR.
    '''

    for root, dirs, files in os.walk(path):

        for path in dirs:
            _fullpath = os.path.join(root, path)
            _mask = "0775"
            octpermissions = oct(stat.S_IMODE ( os.stat ( _fullpath ).st_mode ))
            try:
                if _mask != octpermissions:
                    os.chmod(_fullpath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH | stat.S_ISGID)
                    logger.info("Changed permissions from {} to {} on {}".format(octpermissions,_mask,_fullpath))
                else:
                    logger.debug("{} seems OK {}".format(_fullpath, octpermissions))
            except Exception, err:
                logger.warn("Problem on directory {} {}".format(path, err))


        for path in files:
            _fullpath=os.path.join(root, path)
            _mask = "0664"
            octpermissions = oct(stat.S_IMODE ( os.stat ( _fullpath ).st_mode ))
            try:
                if _mask != octpermissions:
                    os.chmod(_fullpath, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
                    logger.info("Changed permissions from {} to {} on {}".format(octpermissions, _mask, _fullpath))
                else:
                    logger.debug("{} seems OK {}".format(_fullpath, octpermissions))
            except Exception, err:
                logger.warn("Problem on file {} {}".format(path, err))


def dochown(path):
    '''

    '''

    _myuid = os.getuid()
    _mygid = os.getgid()
    _pixar = 8888

    for root, dirs, files in os.walk(path):

        for path in dirs:
            _fullpath = os.path.join(root, path)
            stat_info = os.stat(_fullpath)
            _uid = stat_info.st_uid
            _gid = stat_info.st_gid
            # logger.debug("myuid {} mygid {} uid {} gid {}".format(_myuid,_mygid,_uid,_gid))
            if (_uid != _myuid ) | ( _gid != _pixar):
                try:
                    os.chown(_fullpath, _uid, _pixar)
                    logger.info("Chown from {}:{} to {}:{} on {}".format(_uid, _gid, _myuid, _pixar, _fullpath))

                except Exception, err:
                    logger.warn("Problem on directory {} {}".format(path, err))
            else:
                logger.debug("{} seems OK {}:{}".format(_fullpath, _uid,_gid))

        for path in files:
            _fullpath = os.path.join(root, path)
            stat_info = os.stat(_fullpath)
            _uid = stat_info.st_uid
            _gid = stat_info.st_gid
            # logger.debug("myuid {} mygid {} uid {} gid {}".format(_myuid,_mygid,_uid,_gid))
            if (_uid != _myuid) | (_gid != _pixar):
                try:
                    os.chown(_fullpath, _uid, _pixar)
                    logger.info("Chown from {}:{} to {}:{} on {}".format(_uid, _gid, _myuid, _pixar, _fullpath))

                except Exception, err:
                    logger.warn("Problem on directory {} {}".format(path, err))

            else:
                logger.debug("{} seems OK {}:{}".format(_fullpath, _uid,_gid))



def parseArguments():
    parser = argparse.ArgumentParser(description="Simple sendmail wrapper",  epilog="This is a pain to get right")
    parser.add_argument("-p", dest="path",  help="Path to File or Directory to fix - recursive by default")
    # parser.add_argument("--norecurse", dest="norecurse",   help="No recursive behaviour")
    return parser

def main(path):
    if not os.path.exists(path):
        raise RuntimeError("No path found {}".format(path))
    dochmod(path)
    dochown(path)


if __name__ == '__main__':
    # Main routine - needs one path argument
    parser = parseArguments()
    arguments = parser.parse_args()

    if arguments.path:
        main(arguments.path)
        logger.info("{}".format("Done "))
    else:
        logger.warn("{}".format("You need to provide a path to something, try something like: fix_permissions.py -p "
                                "/tmp/myfile"))


