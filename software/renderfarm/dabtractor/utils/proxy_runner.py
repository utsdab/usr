#!/usr/bin/env rmanpy
# coding=utf-8
'''
A wrapper for running proxys
Should handle finding multiple sequences in a path and possibly a heirachy and
handle multiple proxy definitions, probably my
'''
###############################################################
import logging
import os
import subprocess
import sys
import time

from software.renderfarm.dabtractor import proxys as pt
from software.renderfarm.dabtractor.factories import utils_factory as utils
from software.renderfarm.dabtractor.factories import environment_factory as envfac

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
###############################################################

class Proxytemplate(object):
    # proxy template
    def __init__(self, proxytemplate):
        self.proxytemplae = proxytemplate
        proxypath = os.path.dirname(pt.__file__)
        proxytouse = os.path.join(proxypath, proxytemplate)
        if os.path.isfile(proxytouse):
            self.proxytouse = proxytouse
            logger.debug("Proxy from module is {}".format(proxypath))
            logger.info("Proxy to use is: {}".format(os.path.join(proxypath,proxytemplate)))

        else:
            logger.critical("No proxy template found {}".format(proxytouse))
            sys.exit("No proxy template found")




class ImageSequence(object):
    '''
    This class is an collection of image sequences
    it facilitates generating a nuke command string to generate proxys.
    '''

    def __init__(self, inputthing):
        self.env=envfac.Environment()
        try:
            if os.path.isdir(inputthing):
                self.startingpath = inputthing
            elif os.path.isfile(inputthing):
                self.startingpath = os.path.dirname(inputthing)
            self.sequencelist=[]
            logger.info("Starting Directory: {}".format(self.startingpath))
        except Exception, err:
            logger.warn("Not file or directory: {}".format(inputthing))

    def runlsseq(self):
        # lsseq is in the PATH and should be in the path
        if os.path.isdir(self.startingpath):
            _env = dict(os.environ, my_env_prop='value')
            _lsseqpath = "lsseq"
            _env['PATH'] = '{}:{}'.format(_lsseqpath,_env["PATH"])
            p = subprocess.Popen(["lsseq", "-R", "-O", "-p", "--format", "nuke", self.startingpath],
                                 # env=_env,
                                 stdout=subprocess.PIPE)
            out= p.communicate()[0]
            # output = [ [moviepath, nukefilename, range ], [], [] ]
            for each in out.splitlines():
                try:
                    result=each.split()
                    parentdir=os.path.dirname(os.path.dirname(result[0]))
                    logger.info("Found: {}".format(result))
                    seq=[parentdir, result[0], result[1]]
                    self.sequencelist.append(seq)
                except Exception, err:
                    logger.warn("Sequence error {}".format(err))

    def buildcommand(self, proxytemplate, commandprefixlist=[], commansuffixlist=[]):
        # prepend and post pend more list items to build up a full command to pass to tractor
        self.dabrender = self.env.getdefault("dabrender","path")

        _nuke_proxy_template_path = Proxytemplate("nuke_proxy_720p_prores_v003.py").proxytouse

        _nuke_version = "Nuke{}".format(self.env.getdefault("nuke","version"))
        _nuke_executable = "/Applications/{n}/{n}.app/Contents/MacOS/{n}".format(n=_nuke_version)
        _date = time.strftime("%Y_%m_%d__%H-%M")

        # m 4 says 4 threads
        commandprefixlist=[_nuke_executable, "-V", "0", "-m", "4", "-x", _nuke_proxy_template_path]
        commansuffixlist=[]
        self.fullcommandlist=[]

        for i, seq in enumerate(self.sequencelist):

            nukeinput=[seq[1]]

            _basename = os.path.basename(nukeinput[0])
            # _dirname = os.path.join(seq[0], "movies")

            _dirname = os.path.join(utils.frompathgetuserhome(nukeinput[0]),"renderproxies")


            self.checkoutputpath(_dirname)

            # if not os.path.isdir(_dirname):
            #     os.mkdir(_dirname)

            _seqbasename = ".".join(_basename.split(".")[:-2])
            nukeoutputfile="{}_{}.mov".format(_date,_seqbasename)
            nukeoutput = [os.path.join(_dirname, nukeoutputfile)]

            # forcing to be every frame here
            nukerange=["{}x1".format(seq[2])]

            commandlist=commandprefixlist+nukeinput+nukeoutput+nukerange+commansuffixlist
            self.fullcommandlist.append(commandlist)

    def checkoutputpath(self, directory):
        # check the output path and make it if it doesnt exist
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)

        except Exception, err:
            logger.warn("{} it already exists, {}".format(directory,err))

        if self.isWritable(directory):
            logger.info("{} is writable".format(directory))
        else:
            logger.warn("{} is not writable".format(directory))


    def isWritable(self, directory):
        # check a directory is writeable
        try:
            tmp_prefix = "write_tester";
            count = 0
            filename = os.path.join(directory, tmp_prefix)
            while(os.path.exists(filename)):
                filename = "{}.{}".format(os.path.join(directory, tmp_prefix),count)
                count = count + 1
            f = open(filename,"w")
            f.close()
            os.remove(filename)
            return True
        except Exception, e:
            logger.warn("oops {}".format(e))
            return False


    def runcommand(self):
        for i, seq in enumerate(self.fullcommandlist):
            _env = dict(os.environ, my_env_prop='value')


            try:
                logger.info("Runing command {}".format(" ".join(seq)))
                # p1 = subprocess.Popen(seq, env=_env, stdout=subprocess.PIPE, shell=True)

                p2 = subprocess.Popen(seq,
                                      env=_env,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                output, err = p2.communicate(b"input data to subprocess")
                rc = p2.returncode
                logger.info(output)
                logger.warn(err)
                logger.info("Return Code: {}".format(rc))

            except Exception, runerr:
                logger.warn("Cant run nuke here {}".forman(runerr))
                logger.warn(" ".join(seq))


if __name__ == '__main__':
    logger.info("Running test for {}".format(__name__))
    # filename = "/Volumes/dabrender/work/matthewgidney/testFarm/renderman/maya2016_rms201_cubes/images/maya2016_rms201_cubes.0001.exr"
    # return all the valid image sequences it can find in a list
    logger.info("TESTING")
    dirname = "/Volumes/dabrender/work/matthewgidney/testFarm/renderman/maya2016_rms201_cubes"
    d=ImageSequence(dirname)
    d.runlsseq()
    d.buildcommand(proxytemplate="nuke_proxy_720p_prores_v003.py")
    d.runcommand()
