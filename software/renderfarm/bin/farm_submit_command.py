#!/usr/bin/env rmanpy

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


import tractor.api.author as author
from dabtractor.factories import interface_command_factory as ifac
from dabtractor.factories import command_factory as cfac
from dabtractor.factories import user_factory as ufac
import os, sys

################################
_thisuser = os.getenv("USER")
(_usernumber,_username) =  ufac.FarmUser(_thisuser).query()

if not _username:
    sys.exit("Sorry you dont appear to be a registered farm user {}, try running farm_user.py and then contact matt - "
             "matthew.gidney@uts.edu.au".format(_thisuser))
################################


author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)

if __name__ == '__main__':
    window = ifac.WindowCommand()
    if window.spooljob or window.validatejob is True:
        job = cfac.Bash(
                        command=window.command.get(),
                        startdirectory = window.dirname,
                        # options=window.options.get(),
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
