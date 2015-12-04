#!/opt/pixar/Tractor-2.0/bin/rmanpy

'''
    Using Tractors internal version of python - rmanpy
'''

__author__ = '120988'
import  dabtractor.api.author as author

def usedirmap(input):
    #	generates this return  %D(mayabatch)
    return '%D({thing})'.format(thing=input)

# this can be passed in as args or from UI
proj = "/dabrender/mattg_testing_farm/mattg/TESTING_renderfarm/light_mattg/maya"
scene = "dottyMR_test.0001"
scenefile = "dottyMR_test.0001.ma"
by = 4
start = 1
end = 100

# this is then derived
cmdpath = usedirmap("/usr/autodesk/maya2015-x64/bin/Render")
renderdirectory = usedirmap("%s/images/%s"%(proj,scene))
renderscene = usedirmap("%s/scenes/%s"%(proj,scenefile))
renderproject = usedirmap("%s"%proj)

# building starts here
author.setEngineClientParam(hostname="dabtractor-engine", port=5600, user="mattg", debug=True)
'''
Job attributes
name	type	description
jid	integer	The Job Identifier, the unique, numerical identifier of a job.
owner	string	The user that submitted the job.
spoolhost	string	The host from which the job was submitted.
spoolfile	string	The path to filename of the spooled jobfile.
spoolcwd	string	The working directory of command that spooled the job.
spooladdr	ip adress	The IP address of the host that spooled the job.
title	string	The title of the job.
assignments	encoded string	These are global job variable assignments,
    defined in the Assign section of a job file.
dirmap	json structure	A map for translating paths according to architecture.
tier	string	The name of the tier. A tier is an ordered partitioning of the queue.
priority	float	The priority determines placement of the job in the queue.
crews	string list	The list of crews of the job. This will restrict the job to run on blades which are configured to accept jobs running under those crews.
projects	string list	a list of designations which affects how the active tasks are counted in sharing limits
tags	string list	The names of the limits that will govern all commands of the job. A limit will cap the number of concurrent executions of commands tagged with the limit name.
service	string	The service key expression that will govern all commands of the job. The service key expression is a booean expression that allows commands to be matched with blades that have the capabilities or designation to run them.
envkey	string list	A list of environment key names that establish the environment in which all commands of the job will run.
editpolicy	string	The name of the policy affecting which users can manipulate job.
minslots	integer	The minimum number of slots required to run a command of the job.
maxslots	integer	The maximum number of slots required to run a command of the job.
etalevel	integer	The level of job graph used to estimate remaining time to completion (unused).
afterjids	string	The list of ids of jobs that must finish before this job is started.
maxactive	integer	The maximum number of concurrent active commands allowed for this job.
serialsubtasks	boolean	A boolean value indicating whether subtasks are to be executed serially.
spooltime	timestamp	The time the job was spooled.
pausetime	timestamp	The time job was paused.
aftertime	timestamp	The time after which job will be considered for scheduling.
starttime	timestamp	The time job first had an active task.
stoptime	timestamp	The last time the job had a task that completed.
deletetime	timestamp	The time the job was deleted.
elapsedsecs	integer	The total elapsed seconds the job has been active.
esttotalsecs	integer	The estimated total elapsed task seconds for the job to complete.
numtasks	integer	The number of tasks in the job.
numblocked	integer	The number of blocked tasks in the job. A blocked task requires other tasks to finish before it can become ready, and later, active.
numready	integer	The number of ready tasks in this job. A ready task is a waiting task that does not need any other tasks to finish in order to become active.
numactive	integer	The number of active tasks in the job.
numerror	integer	The number of error tasks in the job.
numdone	integer	The number of done tasks in this job.
maxtid	integer	The highest task id of all tasks of the job, including detached ones. This is used by the engine to manage task id assignment to newly created tasks from expand tasks. Detached tasks are tasks that are not considered for scheduling because they were produced by expand tasks and the job has since been restarted.
maxcid	integer	The highest command id of all commands of the job, including ones of detached tasks. This is used by the engine to manage command id assignement to newly created commands from expand tasks.
comment	string	A user-defined job comment string.
metadata	string	User-defined metadata of the job.
'''
job = author.Job(title="Maya Mental Ray",
                 priority=100,
                 #dirmaps={},
                 envkey=[],
                 metadata="dab render",
                 comment="",
                 tags=[],
                 tier="",
                 projects=[],
                 service="MayaMentalRay")



'''
Task Attributes
name	type	description
jid	integer	The unique identifier of the job the task belongs to.
tid	integer	The Task Identifier, the unique identifier for the task within the job.
title	string	The title of the task.
id	string	The unique string id for the task within the job.
service	string	The service key expression that will govern all commands of the task. The service key expression is a booean expression that allows commands to be matched with blades that have the capabilities or designation to run them.
minslots	integer	The minimum number of slots required to run a command of the task.
maxslots	integer	The maximum number of slots required to run a command of the task.
cids	integer list	A list of command ids of the commands of the task.
serialsubtasks	boolean	A boolean value indicating whether subtasks are to be executed serially.
ptids	integer list	A list of task ids of the parent tasks. Only a task with associated Instances has multiple parents. All child tasks must successfully finish before their parent can become active.
attached	boolean	A boolean value which, if false, indicates the task was result of an expand task that was retried.
state	string	The task state. It can be blocked, ready, active, error, or done.
statetime	timestamp	The time the task became its current state.
readytime	timestamp	The time the task became ready.
activetime	timestamp	The time that the task became active.
currcid	integer	Command id of the command that will run next, or is currently running.
haslog	boolean	A boolean indicating whether task has output in log.
preview	string list	A list of command arguments (argv) of the preview command.
chaser	string list	A list of command arguments (argv) of the chaser command.
progress	float	The task progress, expressed as a percentage value between 0 and 100. This is set when tasks emit ALF_PROGRESS messages.
metadata	string	User-defined metadata of the task.
resumeblock	boolean	A boolean indicating whether the task will automatically resume any resumable ancestor tasks.
retrycount	integer	A counter of the number of passes the task will incur if the job is left to run to completion. A task retry or job restart will increment it if the task had become active at some point.
'''
parent = author.Task(title="Parent",
                     #metadata="",
                     #haslog=False,
                     service="MayaMentalRay")
parent.serialsubtasks = 1

preflight = author.Task(title="Make Image Directory",
                        service="MayaMentalRay")
'''
Command Attributes
name	type	description
jid	integer	The unique identifier of the job the command belongs to.
tid	integer	The unique identifier of the task the command belongs to.
cid	integer	The Command Identifier, the unique identifier for the command within the job.
argv	string list	The list of command arguments representing command.
local	boolean	A boolean that is true if command is to be run on spooling host.
expand	boolean	A boolean that is true if the output of command emits script defining more tasks.
runtype	string	The type of command. Possible values include "normal" and "cleanup".
msg	string	A string value which a blade emits to a pipe to the stdin of the command.
service	string	The service key expression that will govern all commands of the task. The service key expression is a booean expression that allows commands to be matched with blades that have the capabilities or designation to run them.
tags	string list	The names of the limits that will govern all commands of the job. A limit will cap the number of concurrent executions of commands tagged with the limit name.
id	string	The unique string id for the task within the job.
refersto	string	An id of another task or command. Setting this causes the command to run on the same blade that ran the referred task or command ran on.
minslots	integer	The minimum number of slots required to run the command.
maxslots	integer	The maximum number of slots required to run the command.
envkey	string list	A list of environment key names that establish the environment in which the command will run.
retryrcodes	integer list	A list of return codes that will trigger auto-retry logic for the command.
metadata	string	User-defined metadata for the command.
resumewhile	string list	A command argument list that is executed by a blade, or a list of special keywords; either of which determine whether the command is resumable.
resumepin	boolean	A boolean value indicating whether the command should run on the same host when it is resumed.
'''

makedirectory = author.Command(argv=["mkdir", "-p", "%s" % renderdirectory],
                               #runtype="normal",
                               envkey=[])
environment = author.Command(argv=["printenv"],
                             #runtype="normal",
                             envkey=[])

preflight.addCommand(environment)
preflight.addCommand(makedirectory)
parent.addChild(preflight)

rendering=author.Task(title="Maya Rendering", argv=[], service="MayaMentalRay")
rendering.serialsubtasks = 0

# loop through the batch logic
for chunk in range(start, end, by):

    t1="Mental Ray Render %s-%s"%(chunk, chunk+by-1)
    chunk = author.Task(title=t1, argv=["%s" % cmdpath,
                                      "-r", "mr", "-rt", "2",
                                      "-v", "5", "-s", "%s"%chunk,
                                      "-e", "%s" % str(chunk+by-1),
                                      "-rd", "%s" % renderdirectory,
                                      "-proj", "%s" % renderproject,
                                      "%s" % renderscene],  service="MayaMentalRay")

    environment=author.Command(argv=["printenv"])
    chunk.addCommand(environment)
    rendering.addChild(chunk)

parent.addChild(rendering)

proxy = author.Task(title="Make Proxy - ffmpeg", argv=["ffmpeg", "-help"], service="MayaMentalRay")
parent.addChild(proxy)
job.addChild(parent)

'''
Invocation Attributes
name	type	description
jid	integer	The unique identifier of the job the invocation belongs to.
tid	integer	The unique identifier of the task the invocation belongs to.
cid	integer	The unique identifier of the command the invocation belongs to.
iid	integer	The Invocation Identifier, the unique identifier for the invocation within the command.
current	boolean	A boolean value that is true if this is the most recent invocation. When a task is retried, no existing invocations will be considered current.
blade	string	The name of blade the invocation's command is running or ran on.
numslots	integer	The number of slots used by the invocation.
limits	string list	A list of limits in use by the invocation. This value is used to reconstruct the limit counters from currently running invocations should the engine be restarted.
starttime	timestamp	The start time of the invocation.
stoptime	timestamp	The stop time of the invocation.
pid	integer	The process id of the invocation.
rss	float	The resident set size of the process, in GB.
mem	float	The memory usage of the process, in GB.
cpu	float	The current CPU utilization of the process.
elapsedapp	float	The elapsed user time of the process, in seconds.
elapsedsys	float	The elapsed system time of the process, in seconds.
elapsedreal	float	The elapsed wall-clock time of the process, in seconds.
rcode	integer	The return code of the process.
retrycount	integer	The value of the task retry counter when he invocation ran. A task retry or job restart will increment it if the task had become active at some point.
resumecount	integer	A number ordering an interation by its resume pass. iteration nu of times ( the resume of the task retry counter when he invocation ran. A task retry or job restart will increment it if the task had become active at some point.
resumable	boolean	A boolean value that is true if the command can be resumed.
Blade Attributes
name	type	description
name	string	The blade name. It is a unique identifier of the blade, and is typically the blade's hostname.
ipaddr	string	The IP address of the host.
port	integer	The number of the port on which the blade is listening.
osname	string	The name of the operating system on which the blade is running.
osversion	string	The version of operating system on which the blade is running.
boottime	timestamp	The boot time of the host.
numcpu	integer	The number of cpus/cores of the host.
loadavg	float	The CPU load average of the host.
availmemory	float	The available memory of the host, in GB.
availdisk	float	The availble disk space of the host, in GB.
version	string	The Tractor blade version.
profile	string	The profile name used by the blade.
nimby	string	The NIMBY status of the blade.
starttime	timestamp	The start time of the blade process.
numslots	integer	The total number of slots on the blade.
udi	float	The Universal Desirability Index of the blade, which helps certain blades be assigned tasks sooner than other blades. A higher value means the higher the chance of the blade being assigned work.
status	string	A status note for the blade.
heartbeattime	timestamp	The time the blade last contacted the engine.
'''
# print out alf script for sanity
print "#############################\n%s\n############################"%job.asTcl()

# submit the job
#job.spool(owner="mattg")

print help(author)
# print dir(author.Job)
# print help(author.Job)
#
# print dir(author.Task)
# print help(author.Task)
#
# print dir(author.Command)
# print help(author.Command)
