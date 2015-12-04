#!/usr/bin/env rmanpy
'''
	Using Tractors internal version of python - rmanpy

'''

import dabtractor.api.author as author

proj = "/dabrender/mattg_testing_farm/mattg/TESTING_renderfarm/light_mattg/maya"
scene = "dottyMR_test.0001"
scenefile = "dottyMR_test.0001.ma"
by = 4
start = 1
end = 100
cmdpath = "/usr/autodesk/maya2015-x64/bin"

author.setEngineClientParam(hostname="dabtractor-engine", port=5600, user="mattg", debug=True)

job = author.Job(title="Maya Mental Ray", priority=100, service="MayaMentalRay")

parent = author.Task(title="Parent", service="MayaMentalRay")
parent.serialsubtasks = 1

preflight = author.Task(title="Make Image Directory", argv=["mkdir",
                                                            "-p", "%s/images/%s" % (proj, scenefile)],
                        service="MayaMentalRay")

parent.addChild(preflight)

rendering = author.Task(title="Maya Rendering", argv=[], service="MayaMentalRay")
rendering.serialsubtasks = 0

# loop throught the batch logic
for chunk in range(start, end, by):
    t1 = "Mental Ray Render %s-%s" % (chunk, chunk + by - 1)
    chunk = author.Task(title=t1, argv=["%s/Render" % cmdpath,
                                        "-r", "mr",
                                        "-rt", "2",
                                        "-v", "5",
                                        "-s", "%s" % chunk, "-e", "%s" % str(chunk + by - 1),
                                        "-rd", "%s/images/%s" % (proj, scene),
                                        "-proj", "%s" % proj,
                                        "%s/scenes/%s" % (proj, scenefile)], service="MayaMentalRay")

    environment = author.Command(argv=["printenv"])
    chunk.addCommand(environment)
    rendering.addChild(chunk)

parent.addChild(rendering)

proxy = author.Task(title="Make Proxy - ffmpeg", argv=["ffmpeg", "-help"], service="MayaMentalRay")
parent.addChild(proxy)
job.addChild(parent)

print "#############################\n%s\n############################" % job.asTcl()
job.spool(owner="mattg")
