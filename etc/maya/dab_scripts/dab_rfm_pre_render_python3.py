#######  Maya 2022 uses python3

import sys
print(sys.version)

try:
    import pymel.core as pm
    import maya.mel as mel
    import maya.cmds as mc
    import rfm2.api.strings as apistr
    import rfm2.api.scene as apiscene
    import rfm2.api.nodes as apinodes
    import rfm2.ui.maya_ui as mayaui
    import rfm2 as rfm2

except ImportWarning as err:
    print ("********* dab_rfm_pre_render.py import error: %s" % err)
else:
    rmanGlobals = apinodes.rman_globals()
    rfm2.render_with_renderman()


def whichRenderer():
    ### query the renderer
    print ("\nsetting image file prefix for renderer **********************")
    current_renderer = mc.getAttr('defaultRenderGlobals.currentRenderer')
    print("Current Renderer is: {}".format(current_renderer))
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
    print (mc.getAttr('defaultRenderGlobals.imageFilePrefix'))


def setIntegrator(integrator="PxrVisualizer"):
    ### set the integrator
    print ("\nSetting Integrator **********************")
    valid_integrators = ["PxrVisualizer",
                         "PxrDirectLighting",
                         "PxrVCM",
                         "PxrPathTracer",
                         "PxrOcclusion",
                         "PxrValidateBxdf",
                         "PxrDebugShadingContext"]
    try:
        #rfm_integrator = mc.getAttr("renderManRISGlobals.rman__riopt__Integrator_name")
        rfm_integrator = rfm2.api.nodes.get_integrator	(bake = False)

    except Exception as err:
        print ("  {}".format(err))
    else:
        if integrator in valid_integrators:
            print ("  Current Integrator was: {}".format(rfm_integrator))
            print ("  Setting Integrator to {}".format(integrator))
        else:
            print ("  Current Integrator is: {}".format(rfm_integrator))


def setRenderPaths():
    ### This sets up the standard DAB render settings for using renderman 22.3 at uni
    ### We dont use render layers, or rfm versions, ot rfm takes as each render needs
    ### to have its own clean maya file
    ### All AOV's and CAMERAS are rendered

    rmanGlobals = rfm2.api.nodes.rman_globals	(create = False)
    #rfm2.ui.prefs.set_defaults()
    print("\nSetting standard render paths **********************")

    #TODO  warn is layers or multiple cameras found
    iff='<scene>_<aov>.<f4>.<ext>'
    #<scene>_<layer>_<camera>_<aov>.<f4>.<ext>
    rff='<scene>.<f4>.rib'
    #<scene>.<f4>.rib
    iod='<ws>/images/<scene>'
    #<ws>/images/<scene>
    rod='<ws>/renderman/rib/<scene>'
    #<ws>/renderman/rib/<scene>

    mc.setAttr('%s.imageFileFormat' % rmanGlobals,iff, type='string')
    mc.setAttr('%s.imageOutputDir' % rmanGlobals, iod, type='string')
    mc.setAttr('%s.ribFileFormat' % rmanGlobals, rff, type='string')
    mc.setAttr('%s.ribOutputDir' % rmanGlobals, rod, type='string')

    imgOutputDir = mc.getAttr('%s.imageOutputDir' % rmanGlobals)
    imgFileFormat = mc.getAttr('%s.imageFileFormat' % rmanGlobals)
    ribFileFormat = mc.getAttr('%s.ribFileFormat' % rmanGlobals)
    ribOutputDir = mc.getAttr('%s.ribOutputDir' % rmanGlobals)

    #print(rfm2.api.scene.get_image_dir())
    #print(rfm2.api.scene.get_rib_dir()	)
    #print(rfm2.api.scene.is_current_renderer())

    print ("  Rib Output Directory   : {}".format(apistr.expand_string(ribOutputDir)))
    print ("  Rib File Format        : {}".format(apistr.expand_string(ribFileFormat)))
    print ("  Image Output Directory : {}".format(apistr.expand_string(imgOutputDir)))
    print ("  Image File Format      : {}".format(apistr.expand_string(imgFileFormat)))

    mayaui.update_maya_common_tab()


def setAnimation():
    ### turn on animation
    print ("\nTurning on animation **********************")
    animationSetting = mc.getAttr('{}.animation'.format("defaultRenderGlobals"))
    if animationSetting == False:
        print ("  Animation is currently : {}".format(animationSetting))
        mc.setAttr("defaultRenderGlobals.animation", 1)
        mayaui.update_maya_common_tab()
        animationSetting = mc.getAttr('{}.animation'.format("defaultRenderGlobals"))
        print ("  Animation is now on : {}".format(animationSetting))
    else:
        print ("  Animation is on already : {}".format(animationSetting))


def setPasses():
    ### Manage the render passes
    try:
        # passes=mc.mel("rmanGetOutputs rmanFinalGlobals;")
        pass
    except Exception as err:
        print("Error setting basic Passes: {}".format(err))
    else:
        print("Setting basic Passes: {}".format(""))


def renderableCameras():
    ### For now just make sure there is only one rendercamera and return its name.
    print(rfm2.api.scene.current_renderer())
    print(rfm2.api.ui_helpers.get_current_camera()	)


def main():
    print ("\nRFM 24 PreRender Setup **********************")
    print ("Running main from dab_rfm_pre_render_python3")
    # whichRenderer()
    setRenderPaths()
    setAnimation()
    # rfm2.utils.scene_updater.update_scene(log = rfm_log().debug)

if __name__ == "__main__":
    print( "Loaded dab_rfm_pre_render_python3")
    main()


    '''
    RUNNING MEL  : >>>>>> dab_pre_render_mel
             : >>>>>> dab_pre_render_mel
    Error: file: /Volumes/dabrender/usr/etc/maya/dab_scripts/dab_rfm_pre_render_mel.mel 
    line 12: FileNotFoundError: file /Applications/Autodesk/maya2022/Maya.app/Contents/\
    Frameworks/Python.framework/Versions/Current/lib/python3.7/logging/__init__.py line 1116: \
    [Errno 2] No such file or directory: '/Users/120988/pymel.log'
    Error: file: /var/tmp/ASTMP.51038QT6bdQ.mel line 36: Scene /Volumes/dabrender/work/\
    project_work/mattg/TESTING_Renderfarm/Maya/scenes/rfm23/testRender_demo.0006.ma failed to render.
    // Maya exited with status 210
    '''
