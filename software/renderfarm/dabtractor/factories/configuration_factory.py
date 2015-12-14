#!/usr/bin/env rmanpy

"""
    This code holds the configurations for various things

    TODO:
           move all this to a json file and have this method look it up.
"""
import os
import software.renderfarm.dabtractor as dabtractor

# ##############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################

class ConfigurationBase(object):
    """Base configurations - these are the possible options installed"""
    def __init__(self):
        self.mayaversions = ("2016",)
        self.rendermanversions = ("20.2","20.1",)
        self.rendermanrenderers = ("rms-ris", "rms-reyes")
        self.rendermanintegrators = ("pxr", "vcm")
        self.nukeversions = ("9.0v7","9.0v6")
        self.configuration = "base"
        self.projectgroups = ("yr1", "yr2", "yr3", "yr4", "masters", "personal", "admin")
        self.mayarenderers = ("mr", "sw")
        self.renderfarmbin = (os.path.join(os.path.dirname(os.path.dirname(dabtractor.__file__)), "bin"),)
        self.renderfarmmodulepath = (os.path.dirname(os.path.dirname(dabtractor.__file__)),)
        self.renderfarmproxypath = (os.path.join(os.path.dirname(dabtractor.__file__), "proxys"),)
        self.nukedefaultproxytemplate = ("nuke_proxy_720p_prores_v003.py")
        self.dabrenderpath = self.getfromenv("DABRENDERPATH","/Volumes/dabrender")
        self.dabusrpath = self.getfromenv("DABUSR","/Volumes/dabrender")
        self.usermapfilepath = (os.path.join(self.dabusrpath, "custom/map"))
        self.editproxydumppath = (os.path.join(self.dabrenderpath, "renderproxies"))
        self.renderthreads = ("16","8","4","2")
        self.rendermemorys = ("8000","4000","2000")
        self.rendermaxsamples = ("1024","512","256","128","64","32","16")
        self.envtypes = ("work","project",)
        self.envshow = ("matthewgidney",)
        self.envproject = ("testFarm",)
        self.envscene = ("rmsTestFile.ma",)
        self.userid = self.getfromenv("USER")

    def getfromenv(self,key,default=None):
        # try to use an environment variable over the default
        _value = None
        try:
            _value = os.getenv(key, default)
            logger.info("Found {} to be {}".format(key,_value))
        except Exception, e:
            logger.warn("Failed to find anything for {}".format(key))
        return _value

class CurrentConfiguration(ConfigurationBase):
    def __init__(self):
        super(CurrentConfiguration, self).__init__()
        self.configuration = "current"
        self.mayaversion = self.mayaversions[0]
        self.rendermanversion = self.rendermanversions[0]
        self.rendermanrenderer = self.rendermanrenderers[0]
        self.rendermanintegrator = self.rendermanintegrators[0]
        self.renderthread = self.renderthreads[1]
        self.rendermemory = self.rendermemorys[1]
        self.rendermaxsample = self.rendermaxsamples[2]
        self.nukeversion = self.nukeversions[0]
        self.mayarenderer = self.mayarenderers[0]
        self.projectgroup = self.projectgroups[5]
        self.envtype = self.envtypes[0]



if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    AA=CurrentConfiguration()
    print "**** TESTING ****"
    print "latest maya is %s" % AA.mayaversion
    print "latest nuke is %s" % AA.nukeversion
    print "latest renderman is %s" % AA.rendermanversion
    print "latest projects is %s" % AA.projectgroup
    print "renderfarmbin is %s" % AA.renderfarmbin
    print "proxypath is %s" % AA.renderfarmproxypath
    print "usermappath is %s" % AA.usermapfilepath

    _env = os.environ
    _keys = _env.keys()
    _keys.sort()
    print "{:_^80}".format("env")
    for key in _keys:
        print key, _env.get(key)
    print "{:_^80}".format("env")