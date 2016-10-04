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

def main(number,username,year):
    try:
        usermap=uf.Map()
        usermap.adduser(number, username, year)

    except Exception,err:
        logger.warn("Cant add user to map, {}".format(err))
        raise

    try:
        usermap.writecrewformat()
    except Exception, err:
        logger.warn("Cant write crew format, {}".format(err))


    try:
        logger.info("Adding your working directory in dabrender")
        env = uf.EnvType(userid=number)
        env.makedirectory()
    except Exception,err:
        logger.info("Cant make directory {}".format(err))
        raise


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

    try:
        arguments = parseArguments()
        logger.info("Arguments: %s" % arguments)
    except Exception, exitstatus:
        logger.critical("Cant parse args %s" % (arguments))
        sys.exit("ERROR Cant parse arguments %s" % exitstatus)
    try:
        n=arguments.number[0]
        u=arguments.username[0]
        y=arguments.year[0]
    except Exception, exitstatus:
        logger.critical("Cant parse specific number username or year")
        sys.exit("ERROR Cant parse specific arguments %s" % exitstatus)
    else:
        logger.info("number={} username={} year={}".format(n,u,y))
        main(n,u,y)
