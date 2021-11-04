import maya.cmds as cmds
current_renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')
print current_renderer
if current_renderer == 'vray':
    cmds.setAttr('vraySettings.fileNamePrefix', '<Scene>_<Camera>_<Layer>.', type='string')
elif current_renderer == 'mentalRay':
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
elif current_renderer == 'mayaSoftware':
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
elif current_renderer == 'renderManRIS':
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')

cmds.getAttr("renderManRISGlobals.rman__riopt__Integrator_name")

cmds.setAttr("renderManRISGlobals.rman__riopt__Integrator_name", "PxrDefault");
cmds.rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrDefault");



import os

for key in sorted(os.environ.keys()):
    print key, os.environ[key]
