#!/usr/bin/env rmanpy

"""
To do:
    cleanup routine for rib
    create a ribgen then prman version
    check and test options
    run farmuser to check is user is valid

"""
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

import os,sys
import tractor.api.author as author
from software.renderfarm.dabtractor.factories import interface_maya_ribgen_prman_factory as ifac
from software.renderfarm.dabtractor.factories import render_prman_factory as rfac
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.maya.uts_tools import tractor_submit_maya_UI as ts


################################
_thisuser = os.getenv("USER")
# (_usernumber,_username) =  ufac.FarmUser(_thisuser).query()
try:
    u=ufac.User()
    _usernumber=u.number
    _username=u.name
except:
    sys.exit("Sorry you dont appear to be a registered farm user {}, try running farm_user.py and then contact matt - "
             "matthew.gidney@uts.edu.au".format(_thisuser))
################################

author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)

if __name__ == '__main__':
    ts.main()
