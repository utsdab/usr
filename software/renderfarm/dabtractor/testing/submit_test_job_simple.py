#!/usr/bin/env rmanpy
"""
    This script should submit a series of jobs that test each envkey and service
    and runs the main command such as nuke with help only

"""

import tractor.api.author as author
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

mayaversion = "2016"
rendermanversion = "20.1"
nukeversion = "9.0v7"

author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)


# possible tags [ "pixar","rms","maya","nuke","theWholeFarm"]
#  possible projects ["yr4","yr3","yr2","yr1"]
#  possible tiers ["batch","rush","admin","default"]


job = author.Job()
job.title = "Test Simple"
job.priority = 10
# job.envkey = [""]
# job.metadata = ""
job.comment = "LocalUser is "
job.service = "TESTING"
# job.after = datetime.datetime(2012, 12, 14, 16, 24, 5)
# job.afterjids = [1234, 5678]
job.paused = True
job.tier = "admin"
job.projects = ["admin"]
# job.atleast = 2
# job.atmost = 4
# job.newAssignment("tempdir", "/tmp")
# job.newDirMap(src="X:/", dst="//fileserver/projects", zone="UNC")
# job.newDirMap(src="nuke", dst="Nuke", zone="osx")
# job.etalevel = 5
# job.tags = ["tag1", "tag2", "tag3"]
# job.metadata = "show=rat shot=food"
# job.editpolicy = "canadians"
# job.addCleanup(author.Command(argv="/bin/cleanup this"))
# job.newCleanup(argv=["/bin/cleanup", "that"])
# job.addPostscript(author.Command(argv=["/bin/post", "this"]))
# job.newPostscript(argv="/bin/post that")

# task = author.Task()
# task.title = "render layer %d" % i
# task.id = "id%d" % i
# task.chaser = "chase file%i" % i
# task.preview = "preview file%i" % i
# task.service = "services&&more"
# task.atleast = 7
# task.atmost = 8
# task.serialsubtasks = 0
# task.addCleanup(author.Command(argv="/bin/cleanup file%i" % i))

# command = author.Command()
# command.argv = "pixar layer%d.rib" % i
# command.msg = "command message"
# command.service = "cmdservice&&more"
# command.tags = ["tagA", "tagB"]
# command.metrics = "metrics string"
# command.id = "cmdid%i" % i
# command.refersto = "refersto%i" % i
# command.expand = 0
# command.atleast = 1
# command.atmost = 5
# command.samehost = 1
# command.envkey = ["e1", "e2"]
# command.retryrc = [1, 3, 5, 7, 9]
# command.resumewhile = ["/usr/bin/grep", "-q", "Checkpoint", "file.%d.exr" % i]
# command.resumepin = bool(i)


#  possible tags [ "pixar","rms","maya","nuke","theWholeFarm"]
#  possible projects ["yr4","yr3","yr2","yr1"]
#  possible tiers ["batch","rush","admin","default"]


############################ nuke  ####################################

testargv2 = ["/Applications/Nuke9.0v7/Nuke9.0v7.app/Contents/MacOS/Nuke9.0v7", "-help"]

#  possible tags [ "pixar","rms","maya","nuke","theWholeFarm"]

task = author.Task(title="Tasks")
command1 = author.Command(argv=["-help"],
                          envkey=[
                                  "ProjectX SHOW=show SHOT=AAC_001 SCENE=AAC"],
                          tags=["nuke", "theWholeFarm"],
                          service="NukeRender")
task.addCommand(command1)
job.addChild(task)
#########################################################################



try:
    print job.asTcl()
    job.spool(owner="pixar")
except Exception, err:
    logger.critical("Couldnt submit job to spooler %s" % err)

