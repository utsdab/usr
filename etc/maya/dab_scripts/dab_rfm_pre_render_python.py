import os
try:
    import pymel.core as pm
    import maya.mel as mel
    import maya.cmds as mc
    import rfm2.api.strings as apistr
    import rfm2.api.nodes as apinodes
    import rfm2.ui.maya_ui as mayaui
except ImportWarning, err:
    print ("dab_rfm_pre_render.py import error: %s" % err)

def whichRenderer():
    current_renderer = mc.getAttr('defaultRenderGlobals.currentRenderer')
    print "Current Renderer is: {}".format(current_renderer)

    if current_renderer == 'vray':
        mc.setAttr('vraySettings.fileNamePrefix', '<Scene>_<Camera>_<Layer>.', type='string')
    elif current_renderer == 'mentalRay':
        mc.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'mayaSoftware':
        mc.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'renderManRIS':
        mc.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'arnold':
        mc.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')


def setIntegrator(integrator="PxrVisualizer"):
    valid_integrators = ["PxrVisualizer",
                         "PxrDirectLighting",
                         "PxrVCM",
                         "PxrPathTracer",
                         "PxrOcclusion",
                         "PxrValidateBxdf",
                         "PxrDebugShadingContext"]
    try:
        rfm_integrator = mc.getAttr("renderManRISGlobals.rman__riopt__Integrator_name")
    except Exception, err:
        print (err)
    else:
        if integrator in valid_integrators:
            print "Current Integrator was: {}".format(rfm_integrator)
            print "Setting Integrator to {}".format(integrator)
        else:
            print "Current Integrator is: {}".format(rfm_integrator)

def rfm22():
    '''
    This sets up the standard DAB render settings for using renderman 22.3 at uni
    We dont use render layers, or rfm versions, ot rfm takes as each render needs
    to have its own clean maya file
    All AOV's and CAMERAS are rendered
    '''

    rmanGlobals = apinodes.rman_globals()
    #rfm2.ui.prefs.set_defaults()
    print "RFM 22 PreRender Setup......"

    #TODO  warn is layers or multiple cameras found

    iff='<scene>_<aov>.<f4>.<ext>'
    rff='<scene>.<f4>.rib'
    iod='<ws>/images/<scene>'
    rod='<ws>/renderman/rib/<scene>'

    mc.setAttr('%s.imageFileFormat' % rmanGlobals,iff, type='string')
    mc.setAttr('%s.imageOutputDir' % rmanGlobals, iod, type='string')
    mc.setAttr('%s.ribFileFormat' % rmanGlobals, rff, type='string')
    mc.setAttr('%s.ribOutputDir' % rmanGlobals, rod, type='string')

    imgOutputDir = mc.getAttr('%s.imageOutputDir' % rmanGlobals)
    imgFileFormat = mc.getAttr('%s.imageFileFormat' % rmanGlobals)
    ribFileFormat = mc.getAttr('%s.ribFileFormat' % rmanGlobals)
    ribOutputDir = mc.getAttr('%s.ribOutputDir' % rmanGlobals)

    print "Rib Output Directory: {}".format(apistr.expand_string(ribOutputDir))
    print "Rib File Format : {}".format(apistr.expand_string(ribFileFormat))
    print "Image Output Directory: {}".format(apistr.expand_string(imgOutputDir))
    print "Image File Format Directory: {}".format(apistr.expand_string(imgFileFormat))

    mayaui.update_maya_common_tab()

def rfm23():
    '''
    This sets up the standard DAB render settings for using renderman 22.3 at uni
    We dont use render layers, or rfm versions, ot rfm takes as each render needs
    to have its own clean maya file
    All AOV's and CAMERAS are rendered
    '''

    rmanGlobals = apinodes.rman_globals()
    #rfm2.ui.prefs.set_defaults()
    print "RFM 23 PreRender Setup......"

    #TODO  warn is layers or multiple cameras found

    iff='<scene>_<aov>.<f4>.<ext>'
    rff='<scene>.<f4>.rib'
    iod='<ws>/images/<scene>'
    rod='<ws>/renderman/rib/<scene>'

    mc.setAttr('%s.imageFileFormat' % rmanGlobals,iff, type='string')
    mc.setAttr('%s.imageOutputDir' % rmanGlobals, iod, type='string')
    mc.setAttr('%s.ribFileFormat' % rmanGlobals, rff, type='string')
    mc.setAttr('%s.ribOutputDir' % rmanGlobals, rod, type='string')

    imgOutputDir = mc.getAttr('%s.imageOutputDir' % rmanGlobals)
    imgFileFormat = mc.getAttr('%s.imageFileFormat' % rmanGlobals)
    ribFileFormat = mc.getAttr('%s.ribFileFormat' % rmanGlobals)
    ribOutputDir = mc.getAttr('%s.ribOutputDir' % rmanGlobals)

    print "Rib Output Directory: {}".format(apistr.expand_string(ribOutputDir))
    print "Rib File Format : {}".format(apistr.expand_string(ribFileFormat))
    print "Image Output Directory: {}".format(apistr.expand_string(imgOutputDir))
    print "Image File Format Directory: {}".format(apistr.expand_string(imgFileFormat))

    mayaui.update_maya_common_tab()


def setAnimation():
    try:
        print("Setting defaultRenderGlobals:")
        mc.setAttr("defaultRenderGlobals.animation", 1)
    except Exception,err:
        print("Error setting animation: {}".format(err))

def setPasses():
    '''   '''
    try:
        # passes=mc.mel("rmanGetOutputs rmanFinalGlobals;")
        pass
    except Exception, err:
        print("Error setting basic Passes: {}".format(err))
    else:
        print("Setting basic Passes: {}".format(""))

def main():
    print "Running main from dab_rfm_pre_render_python"

if __name__ == "__main__":
    print "Loaded dab_rfm_pre_render_python"
    main()
