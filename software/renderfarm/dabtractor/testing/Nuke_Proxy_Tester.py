#!/usr/bin/env rmanpy

'''
    Using Tractors internal version of python - rmanpy
'''

import tractor.api.author as author
from dabtractor.factories import configuration_factory as config

seq = "/Volumes/dabrender/work/matthewgidney/testFarm/renderman/maya2016_rms201_cubes"

author.setEngineClientParam(hostname="tractor-engine", port=5600, user="mattg", debug=True)

_nuke_envkey = "proxynuke{}".format(config.CurrentConfiguration().nukeversion)
_proxy_runner_cmd = ["proxy_run.py","-s",seq]

job = author.Job(title="Proxy Test With Nuke",
             envkey=[_nuke_envkey],
             priority=100,
             service="NukeRender")

task_proxy = author.Task(title="Proxy Generation", service="NukeRender")
nukecommand = author.Command(argv=_proxy_runner_cmd,
                      service="NukeRender",
                      tags=["nuke", "theWholeFarm"],
                      envkey=[_nuke_envkey])
task_proxy.addCommand(nukecommand)
job.addChild(task_proxy)


print "#############################\n%s\n############################" % job.asTcl()
job.spool(owner="pixar")
