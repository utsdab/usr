#!/usr/bin/env rmanpy


import os
from software.renderfarm.dabtractor.factories import user_factory as uf
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




usermap=uf.Map()
me = os.getenv("USER")
# me = "11712700"  #test

#looking up the map file
try:
    usermap.getuser(me)
    logger.info("You are a farm user: {} {} in year group: {}".format(usermap.getuser(me),
                                                                      usermap.getusername(me)))
except Exception, err:
    logger.info("User {} is not in the map file.  Follow the steps to be added.....".format(me))
    u = uf.UTSuser()
    u.addtomap()
    u.validate()
    u.spool()




