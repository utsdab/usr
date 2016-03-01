#!/usr/bin/env rmanpy
import os,sys
import argparse
from software.renderfarm.dabtractor.factories import user_factory as uf
import tractor.api.author as author


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


'''
This is meant to be run by the farm as pixar user to add a new entry into the json map file

'''

'''
m=uf.Map()
u=uf.User()



me = os.getenv("USER")

#looking up the map file
try:
    m.getuser(me)
    logger.info("You are a farm user: {} {} in year group {}".format(u.name,u.number,u.year))
except Exception, err:
    logger.info("You are not in the map file {}".format(err))
    u = uf.Utsuser()

    ###############
    #make a farm job here so pixar adds the user



self.job = author.Job(title="MentalRay: {} {} {}-{}".format(self.renderusername,
                                                                     self.scenename,self.startframe,self.endframe),
                              priority=10,
                              envkey=[self.envkey_maya,"ProjectX",
                                    "TYPE={}".format(self.envtype),
                                    "SHOW={}".format(self.envshow),
                                    "PROJECT={}".format(self.envproject),
                                    "SCENE={}".format(self.envscene),
                                    "SCENENAME={}".format(self.scenebasename)],
                              metadata="user={} username={} usernumber={}".format(self.user, self.renderusername,
                                                                                  self.renderusernumber),
                              comment="LocalUser is {} {} {}".format(self.user,
                                                                     self.renderusername,
                                                                     self.renderusernumber),
                              projects=[str(self.projectgroup)],

                              tier=_tier,
                              tags=[
                                     "theWholeFarm",
                                    ],
                              service=_service_Testing)
'''

###### do this as pixa and a farm job
# m.adduser("88888","pyschokid","2016")
# print m.getuser("88888")

def parseArguments():
    parser = argparse.ArgumentParser(description="Add user to the Json Map list",
                                     epilog="This should only run as pixar user on the farm")

    parser.add_argument("-u", dest="user",
                        action="append",
                        help="your user number")
    parser.add_argument("-n", dest="username",
                        action="append",
                        help="your user name")
    parser.add_argument("-y", dest="year",
                        action="append",
                        help="year you started")


    return parser.parse_args()

# #####################################################################################################
if __name__ == '__main__':

    arguments = parseArguments()
    logger.debug("%s" % arguments)

    if not (parseArguments()):
        logger.critical("Cant parse args %s" % (arguments))
        sys.exit("ERROR Cant parse arguments")
    else:
        # exitstatus=sendMail(mailto="120988@uts.edu.au",mailsubject="Subject",mailbody="Body of the mail",mailfrom="pixar@uts.edu.au")
        # exitstatus = sendmail(mailto=arguments.mailto[-1:],
        #                       mailsubject=arguments.mailsubject[-1:],
        #                       mailbody=arguments.mailbody[-1:],
        #                       mailfrom=arguments.mailfrom[-1:])

        sys.exit(exitstatus)
