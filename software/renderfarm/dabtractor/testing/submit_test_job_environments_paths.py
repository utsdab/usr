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
testrange = [1, 1, 1]
sleeper = 2

author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)


# possible tags [ "prman","rms","maya","nuke","theWholeFarm"]
#  possible projects ["yr4","yr3","yr2","yr1"]
#  possible tiers ["batch","rush","admin","default"]


job = author.Job()
job.title = "Test Suite Environments and Paths"
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
# command.argv = "prman layer%d.rib" % i
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


#  possible tags [ "prman","rms","maya","nuke","theWholeFarm"]
#  possible projects ["yr4","yr3","yr2","yr1"]
#  possible tiers ["batch","rush","admin","default"]


############################ nuke  ####################################
testGroupName = "Nuke"
testenvkey = ["nuke9.0v7", "setenv SHOW=show", "SHOT=27234-A SCENE=5125"]
testservice = "NukeRender"
testtags = ["nuke", "theWholeFarm"]
testargv1 = ["pwd"]
testargv2 = ["/Applications/Nuke9.0v7/Nuke9.0v7.app/Contents/MacOS/Nuke9.0v7", "-help"]

#  possible tags [ "prman","rms","maya","nuke","theWholeFarm"]

parenttask = author.Task(title="Test %s" % testGroupName, service=testservice)
task = author.Task(title="Iterate %s $frame" % testGroupName)
task.serialsubtasks = 0
subtask1 = author.Task(title="%s %s $frame" % (testargv1[0], testGroupName))
subtask2 = author.Task(title="%s %s $frame" % ("nuke help", testGroupName))
command1 = author.Command(argv=testargv1, envkey=testenvkey, tags=testtags, service=testservice)
command2 = author.Command(argv=testargv2, envkey=testenvkey, tags=testtags, service=testservice)

subtask1.addCommand(command1)
subtask1.newCommand(argv="sleep {}".format(sleeper), envkey=testenvkey, tags=testtags, service=testservice)
subtask2.addCommand(command2)
subtask2.newCommand(argv="sleep {}".format(sleeper), envkey=testenvkey, tags=testtags, service=testservice)
task.addChild(subtask1)
task.addChild(subtask2)

iterate = author.Iterate()
iterate.varname = "frame"
iterate.frm = testrange[0]
iterate.to = testrange[1]
iterate.by = testrange[2]
iterate.addToTemplate(task)

parenttask.addChild(iterate)
job.addChild(parenttask)
#########################################################################

############################ maya  ####################################
testGroupName = "MayaMentalRay"
testenvkey = ["maya2016", "ProjectX SHOT=27234-A SCENE=5125"]
testservice = "MayaMentalRay"
testtags = ["maya", "theWholeFarm"]
testargv1 = ["pwd"]
testargv2 = ["Render", "-r", "mr", "-help"]

#  possible tags [ "prman","rms","maya","nuke","theWholeFarm"]

parenttask = author.Task(title="Test %s" % testGroupName, service=testservice)
task = author.Task(title="Iterate %s $frame" % testGroupName)
task.serialsubtasks = 0
subtask1 = author.Task(title="%s %s $frame" % ("maya pwd", testGroupName))
subtask2 = author.Task(title="%s %s $frame" % ("maya mr  help", testGroupName))
command1 = author.Command(argv=testargv1, envkey=testenvkey, tags=testtags, service=testservice)
command2 = author.Command(argv=testargv2, envkey=testenvkey, tags=testtags, service=testservice)

subtask1.addCommand(command1)
subtask1.newCommand(argv="sleep {}".format(sleeper), envkey=testenvkey, tags=testtags, service=testservice)
subtask2.addCommand(command2)
subtask2.newCommand(argv="sleep {}".format(sleeper), envkey=testenvkey, tags=testtags, service=testservice)
task.addChild(subtask1)
task.addChild(subtask2)

iterate = author.Iterate()
iterate.varname = "frame"
iterate.frm = testrange[0]
iterate.to = testrange[1]
iterate.by = testrange[2]
iterate.addToTemplate(task)

parenttask.addChild(iterate)
job.addChild(parenttask)
#########################################################################



############################ rms  ####################################
testGroupName = "RMS"

testargv1 = ["pwd"]
testargv2 = ["maya", "-help"]
testargv3 = ["pwd"]
testargv4 = ["prman", "-help"]

#  possible tags [ "prman","rms","maya","nuke","theWholeFarm"]

parenttask = author.Task(title="Test %s" % testGroupName,
                         # service=testservice
)
task = author.Task(title="Iterate %s $frame" % testGroupName)
task.serialsubtasks = 0

subtask1 = author.Task(title="%s %s $frame" % ("maya help", testGroupName))
subtask2 = author.Task(title="%s %s $frame" % ("maya pwd", testGroupName))
subtask3 = author.Task(title="%s %s $frame" % ("prman help", testGroupName))
subtask4 = author.Task(title="%s %s $frame" % ("prman pwd", testGroupName))

command1 = author.Command(argv=["maya", "-help"], envkey=["rms-20.1-maya-2016"], tags=["maya", "rms", "theWholeFarm"],
                          service="RfMRibGen")
command2 = author.Command(argv=["printenv"], envkey=["rms-20.1-maya-2016"], tags=["maya", "rms", "theWholeFarm"],
                          service="RfMRibGen")
command3 = author.Command(argv=["prman", "-help"], envkey=["prman-20.1"], tags=["prman", "theWholeFarm"],
                          service="PixarRender")
command4 = author.Command(argv=["printenv"], envkey=["prman-20.1"], tags=["prman", "theWholeFarm"],
                          service="PixarRender")

subtask1.addCommand(command1)
subtask1.newCommand(argv="sleep {}".format(sleeper), envkey=["rms-20.1-maya-2016"],
                    tags=["maya", "rms", "theWholeFarm"])
subtask2.addCommand(command2)
subtask2.newCommand(argv="sleep {}".format(sleeper), envkey=["rms-20.1-maya-2016"],
                    tags=["maya", "rms", "theWholeFarm"])
subtask3.addCommand(command3)
subtask3.newCommand(argv="sleep {}".format(sleeper), envkey=["prman-20.1"], tags=["prman", "theWholeFarm"])
subtask4.addCommand(command4)
subtask4.newCommand(argv="sleep {}".format(sleeper), envkey=["prman-20.1"], tags=["prman", "theWholeFarm"])
task.addChild(subtask1)
task.addChild(subtask2)
task.addChild(subtask3)
task.addChild(subtask4)

iterate = author.Iterate()
iterate.varname = "frame"
iterate.frm = testrange[0]
iterate.to = testrange[1]
iterate.by = testrange[2]
iterate.addToTemplate(task)

parenttask.addChild(iterate)
job.addChild(parenttask)
#########################################################################




try:
    print job.asTcl()
    job.spool(owner="pixar")
except Exception, err:
    logger.critical("Couldnt submit job to spooler %s" % err)

