#!/usr/bin/env rmanpy
import os,sys
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
# me = uf.FarmUser()
# me.build()
m=uf.Map()
u=uf.User()


# print "getuser:{}".format( m.getuser("120988"))
# print "getusername:{}".format( m.getusername("120988"))
# print "getallusers:{}".format( m.getallusers())
# print "getallusers:{}".format( m.getcrewformat())


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




###### do this as pixa and a farm job
# m.adduser("88888","pyschokid","2016")
# print m.getuser("88888")
