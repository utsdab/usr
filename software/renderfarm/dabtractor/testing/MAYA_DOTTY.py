#!/usr/bin/env rmanpy

'''

    Using Tractors internal version of python - rmanpy

'''

import dabtractor.api.author as author


def usedirmap(thing):
    # returns string encapsulated like this %D(mayabatch)
    return '%D({thing})'.format(thing)


proj = "/dabrender/mattg_testing_farm/mattg/TESTING_renderfarm/light_mattg/maya"
scene = "dottyRMS_AOVtest.0042"
scenefile = "dottyRMS_AOVtest.0042.ma"
by = 4
start = 1
end = 100

cmdpath = usedirmap("/usr/autodesk/maya2015-x64/bin/mayabatch")
renderdirectory = usedirmap("%s/images/%s" % (proj, scene))
renderscene = usedirmap("%s/scenes/%s" % (proj, scenefile))
renderproject = usedirmap("%s" % proj)

author.setEngineClientParam(hostname="dabtractor-engine", port=5600, user="mattg", debug=True)

job = author.Job(title="Maya Renderman Studio",
                 envkey=["rms-19.0-maya-2015"],
                 priority=100,
                 service="RfMRender")

parent = author.Task(title="Parent", service="RfMRender")
parent.serialsubtasks = 1

preflight = author.Task(title="Make Image Directory",
                        service="RfMRender")
makedirectory = author.Command(argv=["mkdir", "-p", "%s" % renderdirectory])
environment = author.Command(argv=["printenv"])

preflight.addCommand(environment)
preflight.addCommand(makedirectory)
parent.addChild(preflight)

rendering = author.Task(title="Maya Rendering", argv=[], service="RfMRender")
rendering.serialsubtasks = 0

# loop throught the batch logic
for chunk in range(start, end, by):
    t1 = "Renderman Studio Render %s-%s" % (chunk, chunk + by - 1)
    chunk = author.Task(title=t1, argv=["%s" % cmdpath,
                                        "-r", "rman",
                                        "-rt", "2",
                                        "-v", "5",
                                        "-s", "%s" % chunk, "-e", "%s" % str(chunk + by - 1),
                                        "-rd", "%s" % renderdirectory,
                                        "-proj", "%s" % renderproject,
                                        "%s" % renderscene], service="RfMRender")

    environment = author.Command(argv=["printenv"])
    chunk.addCommand(environment)
    rendering.addChild(chunk)

parent.addChild(rendering)

proxy = author.Task(title="Make Proxy - ffmpeg", argv=["ffmpeg", "-help"], service="RfMRender")
parent.addChild(proxy)
job.addChild(parent)

print "#############################\n%s\n############################" % job.asTcl()
# job.spool(owner="mattg")
