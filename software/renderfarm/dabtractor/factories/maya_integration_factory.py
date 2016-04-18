#!/usr/bin/python
'''
This is a collection of user interfaces for tools
Initially for the tractor submission tools
specificallt for maya hooks - assuming that the interface has been launched inside of maya
'''
# ##############################################################
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################
import os
import sys
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.renderfarm.dabtractor.factories import utils_factory as utilfac

class MayaRenderGlobals(object):
    def __init__(self):
        pass


class RMSGlobals(object):
    def __init__(self):
        pass


if __name__ == '__main__':

    # if running as main - you are essentially testing the factory classes

    sh.setLevel(logging.DEBUG)
    u=ufac.FARMuser()
    logger.info("{}".format( u.__dict__))
    logger.info("hello {}".format(u.username))
    utilfac.printdict(u.__dict__)

