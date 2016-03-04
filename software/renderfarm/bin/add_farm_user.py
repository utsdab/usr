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
This is to be run by the farm as pixar user to add a new entry into the json map file

'''

def main(n="120988",u="matthewgidney",y="staff"):
    try:
        usermap=uf.Map()
        usermap.adduser(n, u, y)
        env=uf.EnvType(userid=n)
        env.makedirectory()

    except Exception,err:
        logger.warn("Cant add user to map, {}".format(err))
        raise

    try:
        logger.info("Adding your working directory in dabrender")
        env = uf.EnvType(userid=me)
        env.makedirectory()
    except Exception,err:
        logger.info("Cant make directory {}".format(err))
        raise


###### do this as pixa and a farm job
# m.adduser("88888","pyschokid","2016")
# print m.getuser("88888")

def parseArguments():
    parser = argparse.ArgumentParser(description="Add user to the Json Map list",
                                     epilog="This should only run as pixar user on the farm")

    parser.add_argument("-n", dest="number",
                        action="append",
                        help="your user number")
    parser.add_argument("-u", dest="username",
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
    try:
        if not (parseArguments()):
            logger.critical("Cant parse args %s" % (arguments))
            sys.exit("ERROR Cant parse arguments")
        else:
            # main(n=arguments.number,u=arguments.username,y=arguments.year)
            main(n="120988",u="matthewgidney",y="staff")
    except Exception, exitstatus:
        sys.exit(exitstatus)
