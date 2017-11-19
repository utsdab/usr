import os
try:
    import maya.cmds as cmds
    import pymel.core as pm
except ImportWarning, err:
    print (err)


#####################
def sayHello():
    print ("RUNNING PYTHON: Starting DAB Pre Render Scripts")

#####################
def whichRenderer():
    current_renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')
    print "Current Renderer is: {}".format(current_renderer)

    if current_renderer == 'vray':
        cmds.setAttr('vraySettings.fileNamePrefix', '<Scene>_<Camera>_<Layer>.', type='string')
    elif current_renderer == 'mentalRay':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'mayaSoftware':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'renderManRIS':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'arnold':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')

def setIntegrator(integrator="PxrVisualizer"):
    '''
    '''
    valid_integrators = ["PxrVisualizer",
                         "PxrDirectLighting",
                         "PxrVCM",
                         "PxrPathTracer",
                         "PxrOcclusion",
                         "PxrValidateBxdf",
                         "PxrDebugShadingContext"]
    try:
        rfm_integrator = cmds.getAttr("renderManRISGlobals.rman__riopt__Integrator_name")
    except Exception, err:
        print (err)
    else:
        if integrator in valid_integrators:
            print "Current Integrator was: {}".format(rfm_integrator)
            print "Setting Integrator to {}".format(integrator)
        else:
            print "Current Integrator is: {}".format(rfm_integrator)



#####################
def setResolution(w,h):
    try:
        print("Setting resolution: {}x{}".format(w,h))
        cmds.setAttr("defaultResolution.width", w)
        cmds.setAttr("defaultResolution.height", h)
    except Exception,err:
        print("Error setting resolution: {}x{}".format(w,h))
    else:
        pass
    finally:
        print("Set resolution: {}".format(""))

#####################
def setAnimation():
    try:
        print("Setting for animation: {}".format(""))
        cmds.setAttr("defaultRenderGlobals.extensionPadding", 4)
        cmds.setAttr("defaultRenderGlobals.byFrameStep", 1)
        # cmds.getAttr("rmanFinalOutputGlobals0.rman__riopt__Display_type")
        cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)
        cmds.setAttr("defaultRenderGlobals.animation", 1)
        cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", 1)
    except Exception,err:
        print("Error seeting animation: {}".format(err))
    else:
        cmds.setAttr("defaultRenderGlobals.imageFormat", 19)

#####################
def setPasses():
    '''
    '''
    try:
        # passes=cmds.mel("rmanGetOutputs rmanFinalGlobals;")
        pass
    except Exception, err:
        print("Error setting basic Passes: {}".format(err))
    else:
        print("Setting basic Passes: {}".format(""))


def showEnvironment():
    try:
        print os.environ[ 'MAYA_LOCATION' ]
        print("--------MAYA_APP_DIR--------")
        print os.environ[ 'MAYA_APP_DIR' ]
        print("--------MAYA_SCRIPT_PATH---------")
        print os.environ[ 'MAYA_SCRIPT_PATH' ]
        print("--------MAYA_PLUG_IN_PATH---------")
        print os.environ[ 'MAYA_PLUG_IN_PATH' ]
        print("--------PYTHONPATH---------")
        print os.environ[ 'PYTHONPATH' ]
        print("--------RDIR---------")
        print os.environ[ 'RDIR' ]
        print("--------RMS_SCRIPT_PATHS---------")
        print os.environ[ 'RMS_SCRIPT_PATHS' ]
    except Exception, err:
        print "WARNING: {}".format(err)
    else:
        pass
    finally:
        print("-----------------")


#################################
def setMe(node="renderManRISGlobals", attr="rman__torattr___motionBlur", value=1):
    # helper to set an attribute

    try:
        _selected = pm.select(node)
    except Exception, err:
        print "Node not found {}".format(node)
        raise()
    else:
        pass
        #print "Node found {}".format(node)


    try:
        _fullAttr = "{}.{}".format(node, attr)
        pm.setAttr(_fullAttr, value)
    except Exception, err:
        print "Cant set {}".format(_fullAttr)
    else:
        print "Set {} to {}".format(_fullAttr, value)


#################################
def getRISAttrs(node="renderManRISGlobals"):
    # helper to show render attribute list
    try:
        _selected = pm.select(node)
    except Exception, err:
        print "Node not found {}".format(node)
        raise(err)
    else:
        for _attr in pm.listAttr(node):
            _nodeAttr = "{}.{}".format(node, _attr)
            _value = pm.getAttr(_nodeAttr)
            _nodeType = pm.nodeType(node)
            print "{} {} {} {}".format(_nodeType, node, _attr , _value)

def setUp():
    #setMe("renderManRISGlobals","rman__torattr___motionBlur",1)
    #setMe("renderManRISGlobals","rman__torattr___cameraBlur",1)
    #setMe("renderManRISGlobals","rman__torattr___motionSamples",4)
    #setMe("renderManRISGlobals","rman__toropt___shutterAngle",180)
    #setMe("renderManRISGlobals","rman__toropt___motionBlurType","frame")
    setMe("renderManRISGlobals","rman__torattr___denoise",0)
    setMe("renderManRISGlobals","rman__riopt__rib_format","binary")
    setMe("renderManRISGlobals","rman__riopt__rib_compression","gzip")
    #setMe("renderManRISGlobals","rman__torattr___linearizeColors",1)


if __name__ == "__main__":
    pass
    #sayhello()
    #setUp()
