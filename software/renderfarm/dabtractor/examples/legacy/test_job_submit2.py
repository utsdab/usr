#!/usr/bin/python



import dabtractor.api.author as author

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
job = author.Job(title="a one-task render job",
                 priority=100,
                 service="PixarRender")

task = author.Task(title="A one-command render task",
                   argv=["/usr/bin/prman", "file.rib"])
job.addChild(task)



'''
For tasks to run serially, so that one task must finish
before another one starts, the task to run first is
declared as a child of the second.
'''
parent = author.Task(title="parent runs second",
                     argv=["/usr/bin/command"])
child = author.Task(title="child runs first",
                    argv=["/usr/bin/command"])
parent.addChild(child)



'''
For tasks to run in parallel, they need only be instantiated
with the same parent.
'''
parent = author.Task(title="comp",
                     argv=["/usr/bin/comp", "fg.tif", "bg.tif"])
parent.newTask(title="render fg",
               argv=["/usr/bin/prman", "fg.rib"])
parent.newTask(title="render bg",
               argv=["/usr/bin/prman", "bg.rib"])

'''
One can optionally run all child tasks of a parent serially
by setting the parent's serialsubtasks to 1.
'''
parent.serialsubtasks = 1


'''
ADDING INSTANCES

Instances are implicitly determined when a task has been
added to more than one parent task.
'''
render1 = author.Task(title="render rib 1", argv=["/usr/bin/prman", "1.rib"])
render2 = author.Task(title="render rib 2", argv=["/usr/bin/prman", "2.rib"])
ribgen = author.Task(title="rib generator", argv=["/usr/bin/ribgen", "1,2", "scene.file"])
render1.addChild(ribgen)
render2.addChild(ribgen)
'''
Instances can also be explicitly defined, passing the
title of the referred task.
'''
render1 = author.Task(title="render rib 1", argv=["/usr/bin/prman", "1.rib"])
render2 = author.Task(title="render rib 2", argv=["/usr/bin/prman", "2.rib"])
ribgen = author.Task(title="rib generator", argv=["/usr/bin/ribgen", "1,2", "scene.file"])
render1.addChild(ribgen)
instance = author.Instance(title="rib generator")
render2.addChild(instance)



'''
ADDING COMMANDS
Tasks typically have one or more commands. Adding a command
to a task can be done using Task.newCommand(), or done in
separate steps of creating a new command and adding it as
a child of a task. The following examples build an equivalent task.
'''
task = author.Task(title="render rib 1")
command = author.Command(argv=["/usr/bin/prman", "1.rib"], service="pixarRender")
task.addCommand(command)
task = author.Task(title="render rib 1")
command = task.newCommand(argv=["/usr/bin/prman", "1.rib"], service="pixarRender")

'''
Additionally, there is a shortcut in which a command can be
instantiated and automatically associated with a task when the task
is created. This is done by setting the argv attribute when initializing a
new task. This approach also works in the author.newTask() method.
'''
task = author.Task(title="render rib 1", argv=["/usr/bin/prman", "1.rib"], service="pixarRender")
task = otherTask.newTask(title="render rib 1", argv=["/usr/bin/prman", "1.rib"], service="pixarRender")

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
task = author.Task(title="multi-command task", service="PixarRender")
copyin = author.Command(argv=["scp", "remote:/path/file.rib", "/local/file.rib"])
task.addCommand(copyin)
render = author.Command(argv=["/usr/bin/prman", "/local/file.rib"])
task.addCommand(render)
copyout = author.Command(argv=["scp", "/local/file.tif", "remote:/path/file.tif"])
task.addCommand(copyout)
task = author.Task(title="multi-command task", service="PixarRender")
task.newCommand(argv=["scp", "remote:/path/file.rib", "/local/file.rib"])
task.newCommand(argv=["/usr/bin/prman", "/local/file.rib"])
task.newCommand(argv=["scp", "/local/file.tif", "remote:/path/file.tif"])

'''Exceptions

When assigning a value to an element's attribute, an exception is raised
if it is not a valid value.
'''
try:
    job.atmost = "three"
except author.AuthorError, err:
    print "you can expect to see this message"

'''More Help
The file <TractorInstallDir>/lib/python2.7/site-packages/dabtractor/api/author/test.py
contains additional examples of API usage.
'''