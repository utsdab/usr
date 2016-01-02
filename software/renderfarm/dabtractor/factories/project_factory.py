#!/usr/bin/python

"""
    This code handles the creation of a user area.
    At UTS the $USER is a number and there is no nice name exposed at all.
    However we can query this from the ldap database using ldapsearch.
    Thus we can definr the concept of renderusername and renderusernumber
    this just need to be in the path some place  dabanim/usr/bin
"""
import os
import sys
import json
import pickle
import shutil
import subprocess
import string
import platform
from software.renderfarm.dabtractor.factories import utils_factory as utils
from software.renderfarm.dabtractor.factories import user_factory as ufac

from pprint import pprint
from software.renderfarm.dabtractor.factories import configuration_factory as config

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

class ProjectBase(object):
    """
    This class is the project structure base
    $DABRENDER/$TYPE/$SHOW/$PROJECT/scenes/$SCENE
    presently $TASK and $SHOT not used
    move this all to a json file template
    """
    def __init__(self):

        self.dabrender = self.alreadyset("DABRENDER","/Volumes/dabrender")
        self.type = self.alreadyset("TYPE","work")
        self.show = self.alreadyset("SHOW","matthewgidney")
        self.project = self.alreadyset("PROJECT","testFarm")
        self.scene = self.alre adyset("SCENE","tesscenefile")
        self.shot = ""  # not used at this moment
        self.task = ""
        self.user = self.alreadyset("USER","120988")
        self.username = self.alreadyset("USERNAME",ufac.Map().getusername(self.user))

    def alreadyset(self, envar, default):
        # look to see if an environment variable is already define an if not return a default value
        try:
            env=os.environ
            val = env[envar]
            logger.debug("{} :: found in environment as {}".format(envar,val))
            return val
        except:
            logger.debug("{} :: not found in environment, setting to default: {}".format(envar,default))
            return default

    def setfromscenefile(self,mayascenefilefullpath):
        if os.path.isfile(mayascenefilefullpath):
            _dirname=os.path.dirname(mayascenefilefullpath)
            _basename=os.path.basename(mayascenefilefullpath)
            _dirbits=os.path.normpath(_dirname).split("/")
            _fullpath=os.path.normpath(mayascenefilefullpath).split("/")
            for i,bit in enumerate(_dirbits):
                if bit=="project" or bit=="work":
                    logger.debug("")
                    self.dabrender="/".join(_dirbits[0:i])
                    logger.debug("DABRENDERPATH: {}".format(self.dabrender))
                    self.type=bit
                    logger.debug("TYPE: {}".format(self.type))
                    self.show=_dirbits[i+1]
                    logger.debug("SHOW: {}".format( self.show))
                    self.project=_dirbits[i+2]
                    logger.debug("PROJECT: {}".format( self.project))
                    self.scenerelative="/".join(_fullpath[i+3:])
                    logger.debug("SCENERELATIVE: {}".format( self.scenerelative))
                    self.scene=_basename
                    logger.debug("SCENE: {}".format(self.scene))
        else:
            logger.warn("Not a file: {}".format(mayascenefilefullpath))



if __name__ == '__main__':

    sh.setLevel(logging.DEBUG)
    logger.info("-------- PROJECT FACTORY TEST ------------")

    p = ProjectBase()
    p.setfromscenefile("/Users/Shared/UTS_Dev/dabrender/work/matthewgidney/matt_maya_project2/scenes/empty.ma")
    p.setfromscenefile("/Users/Shared/UTS_Dev/dabrender/project/albatross/3D/scenes/animation/empty.ma")
    logger.debug("ProjectBase: {}".format(p.__dict__))




