#!/usr/bin/env rmanpy
"""
To do:
    find commonality in render jobs and put it in base class

"""
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
# from software.renderfarm.dabtractor.factories import utils_factory as utils
from software.renderfarm.dabtractor.factories import environment_factory as envfac


class CommandBase(object):
    """
    Base class for all batch jobs
    """
    def __init__(self):
        self.user = os.getenv("USER")
        self.spooljob = False
        self.testing = False
        self.env=envfac.Environment()

        try:
            # get the names of the central render location for the user
            ru = ufac.FARMuser()
            self.renderusernumber = ru.number
            self.renderusername = ru.name
            self.dabrender = ru.dabrender
            self.dabrenderworkpath = ru.dabuserworkpath
            self.initialProjectPath = ru.dabuserworkpath

        except Exception, erroruser:
            logger.warn("Cant get the users name and number back %s" % erroruser)
            sys.exit("Cant get the users name")

        if os.path.isdir(self.dabrender):
            logger.info("Found %s" % self.dabrender)
        else:
            self.initialProjectPath = None
            logger.critical("Cant find central filer mounted %s" % self.dabrender)
            raise Exception, "dabrender not a valid mount point"


class Bash(CommandBase):
    """
    example of standard bash command
    """
    def __init__(self, command="", projectgroup="", email=[1,0,0,0,1,0]):
        super(Bash, self).__init__()
        self.command = command
        self.projectgroup = projectgroup
        self.email = email

    def build(self):
        """
        Main method to build the job
        """

        if self.testing:
            _service_Testing="Testing"
            _tier="admin"

        else:
            _service_Testing=""
            _tier="batch"

        # ################ 0 JOB ################
        self.job = self.env.author.Job(title="Bash Job: {}".format(self.renderusername),
                              priority=10,
                              metadata="user={} realname={}".format(self.user,
                                                                    self.renderusername),
                              comment="LocalUser is {} {} {}".format(self.user,
                                                                     self.renderusername,
                                                                     self.renderusernumber),
                              projects=[str(self.projectgroup)],
                              tier=_tier,
                              tags=["theWholeFarm"],
                              service="ShellServices")


        # ############## 2  BASH ###########
        task_parent = self.env.author.Task(title="Parent")
        task_parent.serialsubtasks = 1
        task_bash = self.env.author.Task(title="Command")

        bashcommand = self.env.author.Command(argv=["bash","-c",self.command])
        task_bash.addCommand(bashcommand)
        task_parent.addChild(task_bash)

        # ############## 7 NOTIFY ###############
        logger.info("email = {}".format(self.email))
        """
        window.emailjob.get(),
        window.emailtasks.get(),
        window.emailcommands.get(),
        window.emailstart.get(),
        window.emailcompletion.get(),
        window.emailerror.get()
        """
        task_notify = self.env.author.Task(title="Notify")
        task_notify.addCommand(self.mail("JOB", "COMPLETE", "blah"))
        task_parent.addChild(task_notify)
        self.job.addChild(task_parent)

    def validate(self):
        #  something
        logger.info("\n\n{:_^80}\n{}\n{:_^80}".format("snip", self.job.asTcl(), "snip"))

    def mail(self, level="Level", trigger="Trigger", body="Render Progress Body"):
        bodystring = "Bash Progress: \nLevel: {}\nTrigger: {}\n\n{}".format(level, trigger, body)
        subjectstring = "FARM JOB: %s " % (self.command)
        mailcmd = self.env.author.Command(argv=["sendmail.py", "-t", "%s@uts.edu.au" % self.user,
                                       "-b", bodystring, "-s", subjectstring])
        return mailcmd

    def spool(self):
        try:
            self.job.spool(owner="pixar")
            logger.info("Spooled correctly")

        except Exception, spoolerr:
            logger.warn("A spool error %s" % spoolerr)


# ##############################################################################
class Rsync(CommandBase):
    """

    """

    def __init__(self,
                 sourcedirectory="",
                 targetdirectory="",
                 spoolipaddress="",
                 spoolhost="",
                 options="",
                 email=[1,0,0,0,1,0]
    ):

        super(Rsync, self).__init__()
        self.sourcedirectory = sourcedirectory
        self.spoolipaddress = spoolipaddress
        self.targetdirectory = targetdirectory
        self.spoolhost = spoolhost
        self.options = options
        self.email = email


    def build(self):
        """
        Main method to build the job
        """
        # ################ 0 JOB ################
        logger.info("Source Directory: {}".format(self.sourcedirectory))
        logger.info("Target Directory:{}".format(self.targetdirectory))
        logger.info("Spool Host: {}".format(self.spoolhost))
        logger.info("Spool Ip Address:{}".format(self.spoolipaddress))
        logger.info("Options: {}".format(self.options))

        self.job = self.env.author.Job(title="Rsync Job: {}".format(self.renderusername),
                              priority=100,
                              # envkey=["maya{}".format(self.mayaversion)],
                              metadata="user={} realname={}".format(self.user,
                                                                    self.renderusername),
                              comment="LocalUser is {} {} {}".format(self.user,
                                                                     self.renderusername,
                                                                     self.renderusernumber),
                              service="MayaMentalRay")

        self.job.newDirMap("/Volumes/dabrender", "/dabrender", "linux")
        self.job.newDirMap("/dabrender", "/Volumes/dabrender", "osx")

        # ############## general commands ############
        env = self.env.author.Command(argv=["printenv"], samehost=1)
        pwd = self.env.author.Command(argv=["pwd"], samehost=1)

        # ############## PARENT #################
        parent = self.env.author.Task(title="Parent Task")
        parent.serialsubtasks = 1

        # ############## 2  RSYNC ###########
        task_loadon = self.env.author.Task(title="Rsync", service="ShellServices")
        _sourceproject = self.sourcedirectory
        _targetproject = self.targetdirectory

        if _sourceproject == _targetproject:
            logger.info("No need to rsync source and target the same project")
            self.sourcetargetsame = True
        else:
            _loadonsource = self.sourcedirectory
            _loadontarget = self.targetdirectory
            logger.info("Loadon Project Source: %s" % _loadonsource)
            logger.info("Loadon Project Target: %s" % _loadontarget)
            loadon = self.env.author.Command(argv=["rsync", "-au", _loadonsource, _loadontarget])
            task_loadon.addCommand(loadon)
            parent.addChild(task_loadon)

        # ############## 7 NOTIFY ###############
        logger.info("email = {}".format(self.email))
        """
        window.emailjob.get(),
        window.emailtasks.get(),
        window.emailcommands.get(),
        window.emailstart.get(),
        window.emailcompletion.get(),
        window.emailerror.get()
        """
        task_notify = self.env.author.Task(title="Notify", service="ShellServices")
        task_notify.addCommand(self.mail("JOB", "COMPLETE", "blah"))
        parent.addChild(task_notify)
        self.job.addChild(parent)

    def validate(self):
        logger.info("\n\n{:_^80}\n{}\n{:_^80}".format("snip", self.job.asTcl(), "snip"))

    def mail(self, level="Level", trigger="Trigger", body="Render Progress Body"):
        bodystring = "Rsync Progress: \nLevel: {}\nTrigger: {}\n\n{}".format(level, trigger, body)
        subjectstring = "FARM JOB: %s %s" % (str(self.sourcedirectory), self.targetdirectory)
        mailcmd = self.env.author.Command(argv=["sendmail.py", "-t", "%s@uts.edu.au" % self.user,
                                       "-b", bodystring, "-s", subjectstring], service="ShellServices")
        return mailcmd

    def spool(self):
        if os.path.exists(self.sourcedirectory):
            try:
                logger.info("Spooled correctly")
                # all jobs owner by pixar user on the farm
                self.job.spool(owner="pixar")
            except Exception, spoolerr:
                logger.warn("A spool error %s" % spoolerr)
        else:
            message = "Cant find source %s" % self.sourcedirectory
            logger.critical(message)
            sys.exit(message)

# ##############################################################################

if __name__ == '__main__':


    rs=Rsync()

    self.env.author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)

    logger.setLevel(logging.DEBUG)
    logger.info("Running test for {}".format(__name__))
    logger.info("START TESTING")
    # TEST = Bash(
    #                startdirectory="/var/tmp",
    #                command="proxy_run.py",
    #                options="-s /Volumes/dabrender/work/jakebsimpson/Assessment_03/renderman/Animation_v03.0066/images",
    #                email=[0,0,0,0,0,0]
    #     )

    TEST = Bash(
               # startdirectory="/var/tmp",
               command="check_farmuser.py",
               # options="",
               email=[0,0,0,0,0,0]
    )

    TEST.build()
    TEST.validate()
    # TEST.spool()
    logger.info("FINISHED TESTING")

