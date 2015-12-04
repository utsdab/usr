#!/usr/bin/python

import dabtractor.api.author as author
import sys
'''
Overview:
In the dabtractor install directory add lib and sitepackahes to the pythonpath

Jobs are built using the Job, Task, Instance, and
Command classes. The job can then be spooled using
the Job.spool() method or displayed using the Job.asTcl()
method.
'''
'''
job = author.Job()
job.title = "a one-task render job"
job.priority = 100
job.service = "PixarRender"
job.newTask(title="A one-command render task",
            argv=["/usr/bin/prman", "file.rib"])
'''
'''
ADDING TASKS

Adding a task to a job can be done using Job.newTask()
(or Task.newTask()) as above, or done in separate steps
of creating a new task and adding it as a child of a
job or other task can be broken down into separate steps.
'''
job1 = author.Job(title="A one-task render job", priority=100, service="PixarRender")
task1 = author.Task(title="A one-command render task", argv=["ls", "-l"])
job1.addChild(task1)
print "\n{}".format(job1.asTcl())



'''
ADDING COMMANDS
Tasks typically have one or more commands. Adding a command
to a task can be done using Task.newCommand(), or done in
separate steps of creating a new command and adding it as
a child of a task. The following examples build an equivalent task.
'''
job2 = author.Job(title="A one-task render job",
                  priority=100,
                  #envkey="",
                  service="PixarRender")

task2 = author.Task(title="render rib 1")
command2 = author.Command(argv=["/usr/bin/prman", "1.rib"], service="pixarRender")
task2.addCommand(command2)
job2.addChild(task2)

task2a = author.Task(title="render rib 2")
command2a = author.Command(argv=["/usr/bin/prman", "2.rib"], service="pixarRender")
task2a.addCommand(command2a)

job2.addChild(task2a)
print "\n{}".format(job2.asTcl())

'''Because each command requires a service key, the API will push the assignment
of the service attribute to the command when this shortcut is used.
If other attributes of a command need to be set, such as the envkey, commands
must be built explicitly using author.Command() or author.Task.newCommand()
instead of using this shortcut.

It is valid for a task to have no commands. For example, a task may serve
to group a subtree of tasks, even though the task itself has no commands
to execute.
'''

'''Multi-command Tasks

When a task has multiple commands, they will be executed serially.
Multiple commands can be associated with a task using successive invocations
of the author.Task.addCommand() or author.Task.newCommand() methods.
'''
job3 = author.Job(title="Typical MayaBatch Render Job",
                  priority=100,
                  envkey=["maya2014"],
                  service="PixarRender")


task3a = author.Task(title="Make output directory",
                     service="PixarRender")
makediectory = author.Command(argv=["mkdir", "/ddd/fff/hhh"])
task3a.addCommand(makediectory)
job3.addChild(task3a)

task3 = author.Task(title="multi-command task", service="PixarRender")
copyin = author.Command(argv=["scp", "remote:/path/file.rib", "/local/file.rib"])
task3.addCommand(copyin)
render = author.Command(argv=["mayabatch", "/local/file.rib"],
#                        envkey="default"
)
task3.addCommand(render)
copyout = author.Command(argv=["scp", "/local/file.tif", "remote:/path/file.tif"])
task3.addCommand(copyout)

remote=author.Command(local=True,tags=["aa"],envkey=["maya2014"],argv=["pwd"])
task3.addCommand(remote)
#task3 = author.Task(title="multi-command task", service="PixarRender")
#task3.newCommand(argv=["scp", "remote:/path/file.rib", "/local/file.rib"])
#task3.newCommand(argv=["/usr/bin/prman", "/local/file.rib"])
#task3.newCommand(argv=["scp", "/local/file.tif", "remote:/path/file.tif"])

job3.addChild(task3)
print "\n{}".format(job3.asTcl())
'''Exceptions

When assigning a value to an element's attribute, an exception is raised
if it is not a valid value.
'''

'''
try:
    job1.atmost = "three"
except author.AuthorError, err:
    print "you can expect to see this message"
'''

'''More Help
The file <TractorInstallDir>/lib/python2.7/site-packages/dabtractor/api/author/test.py
contains additional examples of API usage.
'''