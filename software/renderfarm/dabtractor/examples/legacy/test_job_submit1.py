#!/usr/bin/python



import dabtractor.api.author as author

"""
Overview:
In the dabtractor install directory add lib and sitepackahes to the pythonpath

Jobs are built using the Job, Task, Instance, and
Command classes. The job can then be spooled using
the Job.spool() method or displayed using the Job.asTcl()
method.

This is a test job for UTS farm rollout


"""

job = author.Job(title="a one-task render job", priority=100,
                 service="PixarRender")
job.newTask(title="A one-command render task",
            argv=["/usr/bin/prman",
            "file.rib"], service="pixarRender")
print "\n{0}\n{1}".format("TCL Output",job.asTcl())



"""
Job -title {a one-task render job} -priority {100.0} -service {PixarRender} -subtasks {
  Task {A one-command render task} -cmds {
    RemoteCmd {{/usr/bin/prman} {file.rib}} -service {pixarRender}
  }
}
"""