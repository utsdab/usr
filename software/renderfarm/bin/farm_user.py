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
u=uf.User()
me = os.getenv("USER")

#looking up the map file
try:
    usermap.getuser(me)
    logger.info("You are a farm user: {} {} in year group: {}".format(u.name,u.number,u.year))
except Exception, err:
    logger.info("User {} is not in the map file.  Follow the steps to be added.....".format(err))
    u = uf.UTSuser()
    u.addtomap()
    u.validate()
    u.spool()




