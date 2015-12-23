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
        self.scene = self.alreadyset("SCENE","tesscenefile")
        # self.shot = ""  # not used at this moment
        # self.task = ""
        self.user = self.alreadyset("USER","120988")
        self.username = self.alreadyset("SHOW","matthewgidney")

    def alreadyset(self, envar,default):
        # look to see if an environment variable is already define an if not return a default value
        try:
            env=os.environ
            val = env[envar]
            logger.debug("{} :: found in environment as {}".format(envar,val))
            return val
        except:
            logger.debug("{} :: not found in environment, setting to default: {}".format(envar,default))
            return default

    def test(self):
        pass





if __name__ == '__main__':

    sh.setLevel(logging.DEBUG)
    logger.info("-------- PROJECT FACTORY TEST ------------")

    p = ProjectBase()
    logger.debug("ProjectBase: {}".format(p.__dict__))



