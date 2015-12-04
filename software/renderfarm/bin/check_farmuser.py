#!/usr/bin/env python
import os
from dabtractor.factories import user_factory as fu

# ##############################################################
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################


a = fu.FarmUser(os.getenv("USER"))
logger.info("Found user name >>>> %s" % (a.matchedusername))