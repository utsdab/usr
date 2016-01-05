#!/usr/bin/python

"""
    Useful user functions
"""

import os
import string
import subprocess
import datetime
from software.renderfarm.dabtractor.factories import configuration_factory as config

###############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
###############################################################

def printdict(dict):
    if type(dict) == type({"a": "1"}):
        for i, key in enumerate(dict.keys()):
            print "DICT %s %s: %s" % (i, key, dict.get(key))


def sendmail(mailto,
             mailsubject,
             mailbody,
             mailfrom):
    logger.debug("%s %s %s %s" % (mailto,
                                  mailsubject,
                                  mailbody,
                                  mailfrom))

    sendmail_location = "/usr/sbin/sendmail"  # sendmail location
    p = os.popen("%s -t" % sendmail_location, "w")
    p.write("From: %s\n" % str(mailfrom[0]))
    p.write("To: %s\n" % str(mailto[0]))
    p.write("Subject: %s\n" % str(mailsubject[0]))
    p.write("\n")  # blank line separating headers from body
    p.write("%s" % str(mailbody[0]))
    status = p.close()
    if status != 0:
        print "Sendmail exit status", status
    return status


def getfrompathlist(filetoget, iconpath="ICONPATH"):
    # the path list is much assumed to be much like the environment PATH list separated by :
    # the file is without string
    #returns the matching full path
    _iconpaths = []
    _icon = None

    try:
        _iconpath_paths = os.environ[iconpath].split(os.pathsep)
    except KeyError,e:
        logger("Something wrong with icon path variable {}".format(iconpath))

    for i, _path in enumerate(_iconpaths):
        if os.path.isfile(os.path.join(_path, filetoget)):
            _icon = os.path.join(_path, filetoget)
            logger.debug("Found icon: {}".format(_icon))

    return _icon

def frompathgetuserhome(inputpath):
    try:
        dabrender = config.CurrentConfiguration().dabrenderpath

    except:
        print "err"

    _pathbits = inputpath.split("/")
    _testbits = os.path.join(dabrender, "work").split("/")


    for i, bit in enumerate(_pathbits):
        # print i, bit, _testbits[i]
        try:
            # print i, bit, _testbits[i]
            if not bit == _testbits[i]:
                pass
        except:
            return os.path.join(dabrender,"work",bit)


def getvalues(entries):
    for entry in entries:
        field = entry[0]
        text = entry[1].get()
        logger.info('%s: "%s"' % (field, text))

def usedirmap(inputstring):
    # wraps a command string up as per dirmap needs in pixar tractor eg. %D(mayabatch)
    return '%D({thing})'.format(thing=inputstring)

def expandargumentstring(inputargs=""):
    """
    This takes a string like "-r 2 -l 4" and returns
    {-r} {2} {-l} {4} which is what tractor wants for arguments
    """
    arglist = inputargs.split(" ")
    outputstring = "} {".join(arglist)
    return outputstring

def getfloat(inputstring):
    """
    :param inputstring:
    :return:
    """
    # print "inputstring = >>>%s<<<" % inputstring
    cleanstring = inputstring.strip(string.punctuation)
    # print "cleaned = >>>%s<<" % cleanstring
    return cleanstring

def getnow():
    return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

def truncatepath(inputpath,truncatebit):
    if os.path.isdir(inputpath):
        _pathbits = os.path.abspath(inputpath).split("/")
        _truncated = []
        _matched = False
        for i,bit in enumerate(_pathbits):
            # print i, bit
            # _truncated.append(bit)
            if bit == truncatebit:
                _matched = True
                break
            print i, bit
            _truncated.append(bit)
        _truncatedpath="/".join(_truncated)
        # print inputpath
        # print bit
        # print _truncatedpath
        if os.path.isdir(_truncatedpath):
            return _truncatedpath
    else:
        logger.warn("Not a path when truncating")



class RenderOutput(object):
    '''
    Class to handle render output from renderman etc
    pass in sequences for nuke or proxy generation
    '''
    def __init__(self,filepath=None):
        self.toplevelfilepath=filepath
        logger.debug("Top level filepath: {}".format(self.toplevelfilepath))

    def _runlsseq(self):
        # lsseq is in tractor bin and should be in the path
        filepath=self.toplevelfilepath
        if os.path.isdir(filepath):
            _env=dict(os.environ, my_env_prop='value')
            _lsseqpath="lsseq"
            _env['PATH'] = '{}:{}'.format(_lsseqpath,_env["PATH"])
            p = subprocess.Popen(["lsq","-q","-R","-o","-l", filepath],
                                 stdout=subprocess.PIPE)
            q = subprocess.Popen(["lsseq","-R","-O","-p","-1","--format","nuke", filepath],
                                 stdout=subprocess.PIPE)
            a = q.communicate()[0]
            print a
            b = a.split()
            y=[]
            z=[]
            for i, x in enumerate(b,1):
                # print i
                if i % 2:
                    y.append(x)
                else:
                    z.append(x)





            for j, each in enumerate( zip(y,z) ):
                print j,each




if __name__ == "__main__":
    # testing here
    sh.setLevel(logging.DEBUG)
    # logger.debug("Testing icons={}".format(me.name))
    # logger.debug("Testing number={}".format(me.number))
    # logger.debug("Testing dabrenderwork={}".format(me.dabrenderwork))
    # logger.debug("test getfloat")
    # a='(20.1),'
    # getfloat(a)

    # N=RenderOutput("/Users/Shared/UTS_Jobs/TEACHING_renderman/testFarm/renderman")
    N=RenderOutput("/Users/Shared/UTS_Jobs/TEACHING_renderman/project/renderman")
    N._runlsseq()
    print getnow()

    me = frompathgetuserhome('/Volumes/dabrender/work/matthewgidney/testshite/file.001.exr')
    print "my work directory is",me

    truncatepath("/Users/Shared/UTS_Dev","Shared")

