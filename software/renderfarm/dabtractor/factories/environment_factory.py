#!/usr/bin/python

"""
    This code handles the creation of a user area.
    At UTS the $USER is a number and there is no nice name exposed at all.
    However we can query this from the ldap database using ldapsearch.
    Thus we can define the concept of renderusername and renderusernumber
    this just need to be in the path some place  dabanim/usr/bin
"""
import os
import json
import inspect
from software.renderfarm.dabtractor.factories import utils_factory as utils
# from software.renderfarm.dabtractor.factories import user_factory as ufac
import software.renderfarm.dabtractor as dt
import software.renderfarm as rf

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


print dir(yaml)

class ConfigBase(object):
    def __init__(self):
        self.configjson = os.path.join(os.path.dirname(rf.__file__), "etc","config.json")
        self.defaults = {}
        self.versions = {}
        self.groups = {}
        self.defaultindices = {}
        try:
            _file=open(self.configjson)
        except Exception,err:
            logger.warn(err)
            _file.close()
        else:
            self.config=json.load(_file)
            _keys=self.config.keys()
            _keys.sort()
            for i,k in enumerate(_keys):
                _value=self.config.get(k)
                if type(_value)==type({}):  # has children
                    if _value.has_key("versions"):
                        self.versions[k]=_value.get("versions")
                        self.defaults[k]=_value.get("versions")[_value.get("defaultversionindex")]
                        self.defaultindices[k]=_value.get("defaultversionindex")
                    else:
                        self.versions[k]=None
                        self.defaults[k]=None
                        self.groups[k]=_value
        finally:
            _file.close()
    def getversions(self, key):
        try:
            return self.versions.get(key)
        except Exception, err:
            logger.warn(err)
        else:
            return None

    def getdefault(self, key):
        try:
            return self.defaults.get(key)
        except Exception, err:
            logger.warn(err)
        else:
            return None

    def getdefaultindex(self,key):
        try:
            return self.defaultindices.get(key)
        except Exception, err:
            logger.warn(err)
        else:
            return None

    def getgroupmembers(self,key):
        try:
            return self.groups.get(key)
        except Exception, err:
            logger.warn(err)
        else:
            return None

    def getfromgroup(self,group,member):
        try:
            return self.groups.get(group).get(member)
        except Exception, err:
            logger.warn(err)
        else:
            return None

    def getallkeys(self):
        return self.defaults.keys()

    def getalldefaults(self):
        return self.defaults

    def getallgroups(self):
        return self.groups


class Environment(object):
    """
    This class is the project structure base
    $DABRENDER/$TYPE/$SHOW/$PROJECT/$SCENE
         $SCENE is possible scenes/mayascene.ma - always relative to the project
    presently $TASK and $SHOT not used
    move this all to a json file template
    """

    def __init__(self):
        self.dabrender = self.alreadyset("DABRENDER", "/Volumes/dabrender")
        self.dabusr = self.alreadyset("DABUSR", self.getsoftwarepackagepath())
        self.type = self.alreadyset("TYPE", "user_work")
        self.show = self.alreadyset("SHOW", "")
        self.project = self.alreadyset("PROJECT", "")
        self.scene = self.alreadyset("SCENE", "")
        self.user = self.alreadyset("USER", "")
        self.username = self.alreadyset("USERNAME", "")

    def alreadyset(self, envar, default):
        # look to see if an environment variable is already define an if not return a default value
        try:
            env = os.environ
            val = env[envar]
            logger.debug("{} :: found in environment as {}".format(envar, val))
            return val
        except Exception, err:
            logger.debug("{} :: not found in environment, setting to default: {}".format(envar, default))
            return default

    def setfromscenefile(self, mayascenefilefullpath):
        if os.path.isfile(mayascenefilefullpath):
            _dirname=os.path.dirname(mayascenefilefullpath)
            _basename=os.path.basename(mayascenefilefullpath)
            _dirbits=os.path.normpath(_dirname).split("/")
            _fullpath=os.path.normpath(mayascenefilefullpath).split("/")
            for i, bit in enumerate(_dirbits):
                if bit == "project_work" or bit == "user_work":
                    logger.debug("")
                    self.dabrender="/".join(_dirbits[0:i])
                    logger.debug("DABRENDER: {}".format(self.dabrender))
                    self.type=bit
                    logger.debug("TYPE: {}".format(self.type))
                    self.show=_dirbits[i+1]
                    logger.debug("SHOW: {}".format( self.show))
                    self.project=_dirbits[i+2]
                    logger.debug("PROJECT: {}".format( self.project))
                    self.scene="/".join(_fullpath[i+3:])
                    logger.debug("SCENE: {}".format( self.scene))
        else:
            logger.warn("Cant set from file. Not a file: {}".format(mayascenefilefullpath))

    def getsoftwarepackagepath(self):
        _userfacpath = os.path.dirname(ufac.__file__)
        directories = os.path.normpath(_userfacpath).split("software")
        if len(directories) == 2:
            _base = directories[0]
        else:
            raise "path is bad"
        return directories[0]

    def putback(self):
        os.environ["DABRENDER"] = self.dabrender
        os.environ["TYPE"] = self.type
        os.environ["SHOW"] = self.show
        os.environ["PROJECT"] = self.project
        os.environ["SCENE"] = self.scene
        logger.info("Putback main environment variables")


if __name__ == '__main__':

    sh.setLevel(logging.INFO)
    logger.debug("-------- PROJECT FACTORY TEST ------------")

    e = Environment()
    logger.debug("{}".format(utils.printdict(e.__dict__)))

    e.setfromscenefile("/Volumes/dabrender/user_work/matthewgidney/testFarm/scenes/maya2016_rms_20_8_textured_cubes.ma")
    logger.debug("{}".format(utils.printdict(e.__dict__)))

    JJ = ConfigBase()
    key = "usermapfilepath"
    print "versionlist=",JJ.getversions(key)
    print "defaultversion=",JJ.getdefault(key)
    print "defaultversionindex=",JJ.getdefaultindex(key)
    print "groups=",JJ.getgroupmembers(key)
    print "allkeys=",JJ.getallkeys()
    print "alldefaults=",JJ.getalldefaults()
    print "allgroups=",JJ.getallgroups()

    key = "tractor"
    print "versionlist=",JJ.getversions(key)
    print "defaultversion=",JJ.getdefault(key)
    print "defaultversionindex=",JJ.getdefaultindex(key)
    print "groups=",JJ.getgroupmembers(key)
    print "memberfromgroup=", JJ.getfromgroup(key,"port")
    print "allkeys=",JJ.getallkeys()
    print "alldefaults=",JJ.getalldefaults()
    print "allgroups=",JJ.getallgroups()

    key = "nuke"
    print "versionlist=",JJ.getversions(key)
    print "defaultversion=",JJ.getdefault(key)
    print "defaultversionindex=",JJ.getdefaultindex(key)
    print "groups=",JJ.getgroupmembers(key)
    print "memberfromgroup=", JJ.getfromgroup(key,"port")
    print "allkeys=",JJ.getallkeys()
    print "alldefaults=",JJ.getalldefaults()
    print "allgroups=",JJ.getallgroups()
