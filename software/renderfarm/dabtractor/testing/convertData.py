#!/opt/pixar/Tractor-2.0/bin/rmanpy
__author__ = '120988'


import sys
import os
import dabtractor.testing as td
import json
from dabtractor.factories import user_factory as uf
from dabtractor.factories import configuration_factory as config

###############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
###############################################################

logger.info("Name = %s"%(__name__))


print config.CurrentConfiguration().usermapfilepath


datapath = os.path.join(os.path.dirname(td.__file__),"data")

U = uf.Map(mapfilepath=datapath)

# U.getallusers()
U.getcrewformat()
U.getoldmapformat()


