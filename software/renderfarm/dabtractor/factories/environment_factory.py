#!/usr/bin/python

"""
    This code handles the creation of a user area.
    At UTS the $USER is a number and there is no nice name exposed at all.
    However we can query this from the ldap database using ldapsearch.
    Thus we can definr the concept of renderusername and renderusernumber
    this just need to be in the path some place  dabanim/usr/bin
"""
import os
from software.renderfarm.dabtractor.factories import utils_factory as utils
from software.renderfarm.dabtractor.factories import user_factory as ufac

# ##############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################

class Environment(object):
    """
    This class is the project structure base
    $DABRENDER/$TYPE/$SHOW/$PROJECT/$SCENE
         $SCENE is possible scenes/mayascene.ma - always relative to the project
    presently $TASK and $SHOT not used
    move this all to a json file template
    """
    def __init__(self):
        self.dabrender = self.alreadyset("DABRENDER","/Volumes/dabrender")
        self.dabusr = self.alreadyset("DABUSR",self.getsoftwarepackagepath())
        self.type = self.alreadyset("TYPE","user_work")
        self.show = self.alreadyset("SHOW","matthewgidney")
        self.project = self.alreadyset("PROJECT","testFarm")
        self.scene = self.alreadyset("SCENE","scenes/testscenefile.ma")
        self.user = self.alreadyset("USER","120988")
        self.username = self.alreadyset("USERNAME",ufac.Map().getusername(self.user))

    def alreadyset(self, envar, default):
        # look to see if an environment variable is already define an if not return a default value
        try:
            env=os.environ
            val = env[envar]
            logger.info("{} :: found in environment as {}".format(envar,val))
            return val
        except:
            logger.info("{} :: not found in environment, setting to default: {}".format(envar,default))
            return default

    def setfromscenefile(self,mayascenefilefullpath):
        if os.path.isfile(mayascenefilefullpath):
            _dirname=os.path.dirname(mayascenefilefullpath)
            _basename=os.path.basename(mayascenefilefullpath)
            _dirbits=os.path.normpath(_dirname).split("/")
            _fullpath=os.path.normpath(mayascenefilefullpath).split("/")
            for i,bit in enumerate(_dirbits):
                if bit=="project_work" or bit=="user_work":
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
        _userfacpath=os.path.dirname(ufac.__file__)
        directories = os.path.normpath(_userfacpath).split("software")
        if len(directories)==2:
            _base = directories[0]
        else:
            raise "path is bad"

        return directories[0]

    def putback(self):
        os.environ["DABRENDER"]=self.dabrender
        os.environ["TYPE"]=self.type
        os.environ["SHOW"]=self.show
        os.environ["PROJECT"]=self.project
        os.environ["SCENE"]=self.scene
        logger.info("Putback main environment variables")






if __name__ == '__main__':

    sh.setLevel(logging.DEBUG)
    logger.info("-------- PROJECT FACTORY TEST ------------")

    p = Environment()
    p.setfromscenefile("/Volumes/dabrender/user_work/matthewgidney/testFarm/scenes/dottyRMS.0055.ma")
    print utils.printdict(p.__dict__)

    p.setfromscenefile("/Volumes/dabrender/user_work/matthewgidney/testFarm/dottyRMS.0055.ma")
    logger.debug("ProjectBase: {}".format(p.__dict__))

    print utils.printdict(p.__dict__)




