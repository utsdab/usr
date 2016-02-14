#!/usr/bin/env rmanpy

"""
    This code holds the configurations for various things

    TODO:
           move all this to a json file and have this method look it up.
"""
import os
import software.renderfarm.dabtractor as dt
import inspect
# from   software.renderfarm.dt.factories import utils_factory  as utils

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
        self.configpath = inspect.getfile(self.__class__)
        # logger.info("config path = {}".format(self.configpath))
        # print os.path.abspath(sys.modules[ConfigurationBase.__module__].__file__)
        self.mayaversions = ("2016",)
        self.rendermanversions = ("20.7","20.6","20.5","20.2",)
        self.rendermanrenderers = ("rms-ris", "rms-reyes")
        self.rendermanintegrators = ("FROMFILE","pxr", "vcm","visualiser")
        self.nukeversions = ("9.0v8","9.0v7","9.0v6")
        self.configuration = "base"
        self.projectgroups = ("yr1", "yr2", "yr3", "yr4", "masters", "personal", "admin")
        self.mayarenderers = ("mr", "sw", "FROMFILE")
        self.renderfarmbin = (os.path.join(os.path.dirname(os.path.dirname(dt.__file__)), "bin"),)
        self.renderfarmmodulepath = (os.path.dirname(os.path.dirname(dt.__file__)),)
        self.renderfarmproxypath = (os.path.join(os.path.dirname(dt.__file__), "proxys"),)
        self.nukedefaultproxytemplate = ("nuke_proxy_720p_prores_v003.py")
        self.dabrender = self.getfromenv("DABRENDER", "/Volumes/dabrender")
        self.dabusrpath = self.getfromenv("DABUSR", "/Users/Shared/UTS_Dev/gitRepositories/utsdab/usr/")
        # self.dabusrpath = self.getfromenv("DABUSR", self.getusrinternally())
        self.usermapfilepath = (os.path.join(self.dabusrpath, "etc/map"))
        self.editproxydumppath = (os.path.join(self.dabrender, "renderproxies"))
        self.renderthreads = ("16","8","4","2","1")
        self.ribgenchunks = ("1","2","4","8","16")
        self.rendermemorys = ("8000","4000","2000")
        self.rendermaxsamples = ("FROMFILE","1024","512","256","128","64","32","16")
        self.resolutions = ("FROMFILE","1080p","720p","540p","108p",)
        self.outformats = ("exr",)
        self.envtypes = ("user_work","project_work",)
        self.envshow = ("matthewgidney",)
        self.envproject = ("testFarm",)
        self.envscene = ("rmsTestFile.ma",)
        self.userid = self.getfromenv("USER")

    # def getusrinternally(self):
    #     a= utils.truncatepath(os.path.dirname(self.configpath))
    #     return a

    def getfromenv(self,key,default=None):
        # try to use an environment variable over the default
        _value = None
        try:
            _value = os.getenv(key, default)
            logger.debug("Found {} to be {}".format(key,_value))
        except Exception, e:
            logger.warn("Failed to find anything for {}".format(key))
        return _value

class CurrentConfiguration(ConfigurationBase):
    def __init__(self):
        super(CurrentConfiguration, self).__init__()
        self.user_work=self.envtypes[0]
        self.project_work=self.envtypes[1]
        self.configuration = "current"
        self.mayaversion = self.mayaversions[0]
        self.resolution=self.resolutions[1]
        self.rendermanversion = self.rendermanversions[0]
        self.rendermanrenderer = self.rendermanrenderers[0]
        self.rendermanintegrator = self.rendermanintegrators[0]
        self.renderthread = self.renderthreads[1]
        self.rendermemory = self.rendermemorys[1]
        self.ringenchunk= self.ribgenchunks[0]
        self.rendermaxsample = self.rendermaxsamples[2]
        self.nukeversion = self.nukeversions[0]
        self.mayarenderer = self.mayarenderers[0]
        self.projectgroup = self.projectgroups[5]
        self.envtype = self.envtypes[0]
        self.outformat = self.outformats[0]



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