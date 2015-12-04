#!/usr/bin/env rmanpy
'''
	Using Tractors internal version of python - rmanpy

'''
import dabtractor.api.author as author

author.setEngineClientParam(hostname="dabtractor-engine", port=5600, user="pixar", debug=True)
job = author.Job(title="a one-task render job", priority=100, service="PixarRender")
job.newTask(title="A one-command render task", argv=["snoop.sh"], service="pixarRender")


print "#############################\n%s\n############################" % job.asTcl()

job.spool()

