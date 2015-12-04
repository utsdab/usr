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
from dabtractor.factories import interface_maya_ribgen_prman_factory as ifac
from dabtractor.factories import render_prman_factory as rfac
from dabtractor.factories import user_factory as ufac


################################
_thisuser = os.getenv("USER")
(_usernumber,_username) =  ufac.FarmUser(_thisuser).query()

if not _username:
    sys.exit("Sorry you dont appear to be a registered farm user {}, try running farm_user.py and then contact matt - "
             "matthew.gidney@uts.edu.au".format(_thisuser))
################################


author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)

if __name__ == '__main__':
    window = ifac.WindowPrman()
    if window.spooljob or window.validatejob is True:
        job = rfac.RenderPrman(
                               envtype=window.envtype.get(),
                               envshow=window.envshow.get(),
                               envproject=window.envproject.get(),
                               envscene=window.envscene.get(),
                               mayascenefilefullpath = window.filename,
                               mayaprojectpath=window.dirname,
                               mayaversion=window.mayaversion.get(),
                               rendermanversion=window.rendermanversion.get(),
                               startframe=int(window.sf.get()),
                               endframe=int(window.ef.get()),
                               byframe=int(window.bf.get()),
                               outformat=window.outformat.get(),
                               resolution=window.resolution.get(),
                               renderthreads=window.renderthread.get(),
                               rendermemory=window.rendermemory.get(),
                               rendermaxsamples=window.rendermaxsamples.get(),
                               options=window.options.get(),
                               projectgroup=window.projectgroup.get(),
                               skipframes=window.skipframes.get(),
                               makeproxy=window.makeproxy.get(),
                               email=[
                                       window.emailjob.get(),
                                       window.emailtasks.get(),
                                       window.emailcommands.get(),
                                       window.emailstart.get(),
                                       window.emailcompletion.get(),
                                       window.emailerror.get()
                               ]
        )

        try:
            job.build()
        except Exception, buildError:
            logger.warn("Something wrong building job %s" % buildError)

        if window.spooljob is True:

            try:
                job.validate()
                job.spool()
            except Exception, spoolError:
                logger.warn("Something wrong spooling job %s" % spoolError)

        if window.validatejob is True:
            try:
                job.validate()
            except Exception, validateError:
                logger.warn("Something wrong validating job %s" % validateError)
