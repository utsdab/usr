#!/usr/bin/env python
import os
from dabtractor.python.factories import farm_user as fu

# ##############################################################
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
# sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################


a = fu.FarmUser(os.getenv("USER"))
logger.info("Found user name >>>> %s" % (a.matchedusername))
